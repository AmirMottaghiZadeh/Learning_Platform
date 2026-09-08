"""Read-side assembly for the /me/* screens."""

from datetime import timedelta

from django.apps import apps as django_apps
from django.utils import timezone

from apps.lessons.selectors import lesson_groups

from .models import DailyStudy, Mistake
from .services import get_plan, get_progress


def _display_name(user):
    profile = getattr(user, "learner_profile", None)
    if profile and profile.display_name:
        return profile.display_name
    return user.first_name or user.get_username()


def _next_chapter(groups):
    for group in groups:
        for sub in group["subgroups"]:
            if sub["done"] < sub["total"]:
                return {
                    "code": sub["code"],
                    "name_fa": sub["name_fa"],
                    "name_en": sub["name_en"],
                    "group_code": group["code"],
                    "group_name_fa": group["name_fa"],
                    "group_name_en": group["name_en"],
                }
    return None


def _mastery_pct(groups):
    total = sum(s["total"] for g in groups for s in g["subgroups"])
    done = sum(s["done"] for g in groups for s in g["subgroups"])
    return round(100 * done / total) if total else 0


def _leitner_focus_row(user):
    """Only present once the flashcards app is installed and has due cards."""
    if not django_apps.is_installed("apps.flashcards"):
        return None
    try:
        from apps.flashcards.services import due_card_count
    except Exception:
        return None
    due = due_card_count(user)
    if not due:
        return None
    minutes = max(2, round(min(due, 10) * 0.4))
    return {
        "kind": "leitner",
        "title_fa": f"{min(due, 10)} فلش‌کارت سررسیده",
        "title_en": f"{min(due, 10)} due flashcards",
        "sub_fa": f"از {due} کارت لایتنر امروز",
        "sub_en": f"of {due} Leitner cards today",
        "minutes": minutes,
        "count": min(due, 10),
    }


def dashboard(user):
    progress = get_progress(user)
    groups = lesson_groups(user)
    next_chapter = _next_chapter(groups)

    rows = []
    leitner = _leitner_focus_row(user)
    if leitner:
        rows.append(leitner)

    top_mistake = (
        Mistake.objects.filter(user=user, resolved=False).order_by("-count", "-last_seen").first()
    )
    if top_mistake:
        minutes = max(2, round(top_mistake.count * 0.75))
        rows.append({
            "kind": "mistake",
            "title_fa": f"سؤال‌های «{top_mistake.topic_fa}»",
            "title_en": f"Questions on {top_mistake.topic_en}",
            "sub_fa": f"پرتکرارترین اشتباه تو — {top_mistake.count} بار",
            "sub_en": f"Your top recurring mistake — {top_mistake.count}x",
            "minutes": minutes,
            "mistake_id": top_mistake.id,
        })

    if next_chapter:
        rows.append({
            "kind": "lesson",
            "title_fa": f"شروع فصل «{next_chapter['name_fa']}»",
            "title_en": f"Start the {next_chapter['name_en']} chapter",
            "sub_fa": f"{next_chapter['group_name_fa']} · {next_chapter['code']}",
            "sub_en": f"{next_chapter['group_name_en']} · {next_chapter['code']}",
            "minutes": 2,
            "atc_code": next_chapter["code"],
        })

    return {
        "greeting_name": _display_name(user),
        "streak_days": progress.streak_days,
        "xp": progress.xp,
        "next_chapter": next_chapter,
        "focus_session": {
            "rows": rows,
            "total_minutes": sum(r["minutes"] for r in rows),
        },
    }


def week_bars(user):
    today = timezone.localdate()
    week_start = today - timedelta(days=(today.weekday() - 5) % 7)  # Saturday
    minutes_by_day = dict(
        DailyStudy.objects.filter(
            user=user, day__gte=week_start, day__lt=week_start + timedelta(days=7)
        ).values_list("day", "minutes")
    )
    return [minutes_by_day.get(week_start + timedelta(days=i), 0) for i in range(7)]


def statistics(user):
    progress = get_progress(user)
    groups = lesson_groups(user)
    return {
        "week_bars": week_bars(user),
        "accuracy_pct": progress.accuracy_pct,
        "quizzes": progress.total_quizzes,
        "reviews": progress.total_reviews,
        "minutes": progress.total_minutes,
        "mastery_pct": _mastery_pct(groups),
    }
