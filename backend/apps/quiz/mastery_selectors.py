"""Per-topic and overall quiz performance, computed straight from past
QuizSession rows -- no separate tracking table. A topic's "mastery" is the
average score (%) across the learner's finished sessions in it; a session
with `atc_code` set still counts toward its parent topic's (`category`)
mastery, since narrowing to one chapter doesn't change which topic it's
part of.
"""

from django.db.models import Avg, F, FloatField
from django.db.models.functions import Cast

from .models import DRUG_SESSION_CATEGORY, QuizSession

WEAK_TOPIC_THRESHOLD_PCT = 60


def _finished_sessions(user):
    return QuizSession.objects.filter(user=user, finished_at__isnull=False)


def _finished_topic_sessions(user):
    """`_finished_sessions`, minus single-drug self-tests -- those aren't
    attempts at a study topic, so they don't belong in the per-topic
    mastery map."""
    return _finished_sessions(user).exclude(category=DRUG_SESSION_CATEGORY)


def topic_mastery_map(user) -> dict:
    """{topic_key: avg_score_pct} across every topic this learner has ever
    finished a quiz in. A topic absent from the map has never been attempted
    (the caller renders that as "new", not as 0%)."""
    rows = (
        _finished_topic_sessions(user)
        .values("category")
        .annotate(pct=Avg(Cast(F("score"), FloatField()) * 100 / F("question_count")))
    )
    return {row["category"]: round(row["pct"]) for row in rows if row["pct"] is not None}


def weak_topics_count(user, threshold: int = WEAK_TOPIC_THRESHOLD_PCT) -> int:
    mastery = topic_mastery_map(user)
    return sum(1 for pct in mastery.values() if pct < threshold)


def best_score_pct_for_topic(user, topic_key: str, exclude_session_id: int | None = None):
    """The learner's best past score (%) in this topic, excluding the
    just-finished session itself -- for the results screen's "better than
    your previous best" comparison. None if this is their first attempt."""
    qs = _finished_sessions(user).filter(category=topic_key)
    if exclude_session_id is not None:
        qs = qs.exclude(pk=exclude_session_id)
    best = None
    for session in qs.only("score", "question_count"):
        if not session.question_count:
            continue
        pct = round(100 * session.score / session.question_count)
        if best is None or pct > best:
            best = pct
    return best
