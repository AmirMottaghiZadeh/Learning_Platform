from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from .models import LeagueResult, LeagueSeason

LEAGUE_QUESTION_COUNT = 50
LEAGUE_RULE_VERSION = "mvp-weekly-league-v1"

def round_metric(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_week_bounds(now=None):
    current = timezone.localtime(now or timezone.now())
    week_start = (current - timedelta(days=current.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return week_start, week_start + timedelta(days=7)


def season_key_for(starts_at):
    year, week, _ = starts_at.isocalendar()
    return f"{year}-W{week:02d}"


def get_current_season(*, product_id="k_game", now=None):
    starts_at, ends_at = get_week_bounds(now)
    key = season_key_for(starts_at)
    season, _ = LeagueSeason.objects.get_or_create(
        product_id=product_id,
        key=key,
        defaults={
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": LeagueSeason.STATUS_ACTIVE,
        },
    )
    return season


def list_league_seasons(*, product_id="k_game", limit=12):
    return LeagueSeason.objects.filter(product_id=product_id).order_by("-starts_at")[:limit]


def session_product_id(session):
    question = (
        session.questions
        .select_related("knowledge_source")
        .filter(knowledge_source__isnull=False)
        .order_by("order")
        .first()
    )
    if question and question.knowledge_source_id:
        return question.knowledge_source.product_id
    return "k_game"


def save_league_result(session):
    product_id = session_product_id(session)
    season = get_current_season(product_id=product_id)
    answered = session.answers.count()
    wrong = answered - session.correct_count
    percent = round((session.correct_count / answered) * 100) if answered else 0
    score_per_question = round_metric(Decimal(session.score) / Decimal(LEAGUE_QUESTION_COUNT))
    time_bonus = round_metric(Decimal(session.time_remaining_total) / Decimal(LEAGUE_QUESTION_COUNT))
    league_rating = score_per_question + time_bonus
    duration = max(1, int(((session.finished_at or timezone.now()) - session.started_at).total_seconds()))
    result = LeagueResult.objects.create(
        user=session.user, session=session, product_id=product_id,
        season=season, season_key=season.key,
        topic_key=session.topic_key, raw_score=session.score,
        score_per_question=score_per_question, time_remaining_total=session.time_remaining_total,
        time_bonus=time_bonus, league_rating=league_rating, answered=answered,
        correct=session.correct_count, wrong=wrong, percent=percent, duration_seconds=duration,
        league_rule_version=LEAGUE_RULE_VERSION,
    )
    result.rank_snapshot = calculate_result_rank(result)
    result.save(update_fields=["rank_snapshot"])
    return result


def base_leaderboard_queryset(*, product_id="k_game", topic_key=None, season_key=None):
    if season_key is None:
        season_key = get_current_season(product_id=product_id).key
    qs = (
        LeagueResult.objects
        .select_related("user", "season")
        .filter(product_id=product_id, season_key=season_key)
        .order_by("-league_rating", "-raw_score", "-percent", "-time_remaining_total", "created_at")
    )
    if topic_key:
        qs = qs.filter(topic_key=topic_key)
    return qs


def calculate_result_rank(result):
    better_results = LeagueResult.objects.filter(
        product_id=result.product_id,
        season_key=result.season_key,
        topic_key=result.topic_key,
    ).filter(
        Q(league_rating__gt=result.league_rating)
        | Q(league_rating=result.league_rating, raw_score__gt=result.raw_score)
        | Q(
            league_rating=result.league_rating,
            raw_score=result.raw_score,
            percent__gt=result.percent,
        )
        | Q(
            league_rating=result.league_rating,
            raw_score=result.raw_score,
            percent=result.percent,
            time_remaining_total__gt=result.time_remaining_total,
        )
        | Q(
            league_rating=result.league_rating,
            raw_score=result.raw_score,
            percent=result.percent,
            time_remaining_total=result.time_remaining_total,
            created_at__lt=result.created_at,
        )
    )
    return better_results.count() + 1


def get_leaderboard_entries(*, product_id="k_game", topic_key=None, season_key=None, limit=100):
    qs = base_leaderboard_queryset(
        product_id=product_id,
        topic_key=topic_key,
        season_key=season_key,
    )
    entries = []
    seen_users = set()
    for result in qs:
        if result.user_id in seen_users:
            continue
        seen_users.add(result.user_id)
        entries.append(
            {
                "rank": len(entries) + 1,
                "result": result,
            }
        )
        if len(entries) >= limit:
            break
    return entries


def get_user_league_rank(user, *, product_id="k_game", topic_key=None, season_key=None):
    entries = get_leaderboard_entries(
        product_id=product_id,
        topic_key=topic_key,
        season_key=season_key,
        limit=1000,
    )
    for entry in entries:
        if entry["result"].user_id == user.id:
            return {
                "rank": entry["rank"],
                "result": entry["result"],
                "total_participants": len(entries),
            }
    return {
        "rank": None,
        "result": None,
        "total_participants": len(entries),
    }


def get_league_summary(user, *, product_id="k_game", topic_key=None, season_key=None, limit=100):
    season = (
        LeagueSeason.objects.filter(product_id=product_id, key=season_key).first()
        if season_key
        else get_current_season(product_id=product_id)
    )
    resolved_season_key = season.key if season else season_key
    leaderboard = get_leaderboard_entries(
        product_id=product_id,
        topic_key=topic_key,
        season_key=resolved_season_key,
        limit=limit,
    )
    rank = get_user_league_rank(
        user,
        product_id=product_id,
        topic_key=topic_key,
        season_key=resolved_season_key,
    )
    return {
        "season": season,
        "season_key": resolved_season_key or "",
        "topic_key": topic_key or "",
        "leaderboard": leaderboard,
        "my_rank": rank,
        "total_participants": rank["total_participants"],
        "rule_version": LEAGUE_RULE_VERSION,
    }
