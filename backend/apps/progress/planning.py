"""Study-plan generation and topic mastery.

Deliberately separate from `services.py` (which just records what already
happened) and `selectors.py` (which just reads): this module *decides* what a
learner should study next, so its logic -- the mastery formula, the
generation algorithm, replanning -- stays out of both the views and the other
apps that feed it signals (lessons/flashcards/quiz).

Three planning models share this one module because they share the same
underlying signals (`ReadDrug`, quiz answers, Leitner boxes) -- see
`models.StudyPlan` for what distinguishes "goal" from "maintenance".
"""

from datetime import timedelta

from django.utils import timezone

from apps.flashcards.models import MAX_BOX, LeitnerCard
from apps.flashcards.services import due_card_count
from apps.lessons.data.study_topics import STUDY_TOPICS
from apps.lessons.models import ChapterProgress
from apps.lessons.selectors import lesson_groups, slugs_for_topic, topic_chapters, topic_progress
from apps.quiz.models import QuizAnswer

from .models import Mistake, StudyPlan, StudyPlanItem

LESSON_MINUTES_PER_CHAPTER = 10
QUIZ_MINUTES = 10
FLASHCARD_MINUTES = 8
MISTAKE_REVIEW_MINUTES = 10

# Assessment performance is the strongest signal of real mastery, recall
# (flashcard retention) the next strongest, and merely having read the
# material the weakest -- see the Mastery section of the planning spec this
# implements. Whichever signals have no data yet (quiz/flashcards never
# touched) drop out and the rest are renormalised, so a topic still gets a
# mastery score from completion alone before the learner has quizzed on it.
MASTERY_WEIGHTS = {"completion": 0.3, "quiz": 0.4, "recall": 0.3}

_NEVER = timezone.now() - timedelta(days=365 * 100)


def _topic_by_key(topic_key):
    return next((t for t in STUDY_TOPICS if t["key"] == topic_key), None)


def _quiz_accuracy_for_slugs(user, slugs):
    if not slugs:
        return None
    qs = QuizAnswer.objects.filter(
        question__session__user=user, question__subject_slug__in=slugs
    )
    total = qs.count()
    if not total:
        return None
    correct = qs.filter(is_correct=True).count()
    return round(100 * correct / total)


def _flashcard_recall_for_slugs(user, slugs):
    if not slugs:
        return None
    boxes = list(
        LeitnerCard.objects.filter(user=user, ingredient__slug__in=slugs).values_list(
            "box", flat=True
        )
    )
    if not boxes:
        return None
    avg_box = sum(boxes) / len(boxes)
    return round(100 * (avg_box - 1) / (MAX_BOX - 1))


def topic_mastery(user, topic_key):
    """0-100: how well the learner actually knows this topic, as distinct
    from how much of it they've merely read (see `topic_progress` for that)."""
    slugs = slugs_for_topic(topic_key)
    signals = {"completion": topic_progress(user, topic_key)["pct"]}
    quiz_pct = _quiz_accuracy_for_slugs(user, slugs)
    if quiz_pct is not None:
        signals["quiz"] = quiz_pct
    recall_pct = _flashcard_recall_for_slugs(user, slugs)
    if recall_pct is not None:
        signals["recall"] = recall_pct

    total_weight = sum(MASTERY_WEIGHTS[k] for k in signals)
    return round(sum(v * MASTERY_WEIGHTS[k] for k, v in signals.items()) / total_weight)


# -- generation -------------------------------------------------------------


def _groups_by_topic(user):
    """`lesson_groups(user)` rebuilds its ingredient index from scratch, so
    every generation call fetches it exactly once and the topic loops below
    share that one result instead of re-querying per topic."""
    return {g["code"]: g for g in lesson_groups(user)}


def _topic_backlog(topic_key, group):
    """Ordered work units for one topic: unread chapters first, then one
    quiz and one flashcard pass over the whole topic."""
    topic = _topic_by_key(topic_key)
    if not topic:
        return []
    chapters = _with_chapters(group)
    items = []
    for chapter in chapters["unread"]:
        items.append({
            "activity_type": StudyPlanItem.LESSON,
            "topic_key": topic_key,
            "atc_code": chapter["code"],
            "estimated_minutes": LESSON_MINUTES_PER_CHAPTER,
            "reason_fa": f"هنوز فصل «{chapter['name_fa']}» را نخوانده‌ای.",
            "reason_en": f"You haven't read the {chapter['name_en']} chapter yet.",
        })
    if chapters["all"]:
        items.append({
            "activity_type": StudyPlanItem.QUIZ,
            "topic_key": topic_key,
            "atc_code": "",
            "estimated_minutes": QUIZ_MINUTES,
            "reason_fa": f"یک آزمون کوتاه برای سنجش تسلطت روی «{topic['name_fa']}».",
            "reason_en": f"A short quiz to check your grasp of {topic['name_en']}.",
        })
        items.append({
            "activity_type": StudyPlanItem.FLASHCARDS,
            "topic_key": topic_key,
            "atc_code": "",
            "estimated_minutes": FLASHCARD_MINUTES,
            "reason_fa": f"مرور فلش‌کارتی داروهای «{topic['name_fa']}».",
            "reason_en": f"Flashcard review for the {topic['name_en']} drugs.",
        })
    return items


def _study_days(days, start, end):
    """Calendar dates in [start, end] whose weekday is enabled in `days`
    (index 0..6 = Sat..Fri, matching `models.default_week`)."""
    out = []
    d = start
    while d <= end:
        idx = (d.weekday() + 2) % 7  # Mon=0..Sun=6 -> Sat=0..Fri=6
        if days[idx]:
            out.append(d)
        d += timedelta(days=1)
    return out


def _pack_into_days(backlog, study_days, daily_minutes):
    """Greedily fills each study day up to `daily_minutes` before spilling
    into the next one. A single item longer than the daily budget still
    gets placed (as the only thing that day) rather than blocking forever.
    `study_days` is never empty -- callers always fall back to [today]."""
    buckets = {d: [] for d in study_days}
    minutes_used = dict.fromkeys(study_days, 0)
    days_left = list(study_days)
    for item in backlog:
        while (
            days_left
            and minutes_used[days_left[0]] > 0
            and minutes_used[days_left[0]] + item["estimated_minutes"] > daily_minutes
        ):
            days_left.pop(0)
        if not days_left:
            return buckets, False
        day = days_left[0]
        buckets[day].append(item)
        minutes_used[day] += item["estimated_minutes"]
    return buckets, True


def _flatten(buckets):
    rows = []
    for day in sorted(buckets):
        for order, item in enumerate(buckets[day]):
            rows.append({**item, "day": day, "order": order})
    return rows


def _with_chapters(group):
    chapters = group["subgroups"] if group else []
    return {
        "all": chapters,
        "unread": [c for c in chapters if c["done"] < c["total"]],
    }


def _goal_items(user, plan):
    groups = _groups_by_topic(user)
    backlog = []
    for topic_key in plan.topic_keys:
        backlog.extend(_topic_backlog(topic_key, groups.get(topic_key)))

    today = timezone.localdate()
    end = max(plan.deadline or today, today)
    study_days = _study_days(plan.days, today, end) or [today]
    buckets, fits = _pack_into_days(backlog, study_days, plan.daily_minutes)
    return _flatten(buckets), fits


def _stalest_read_chapter(user, groups, topic_keys):
    """The fully-read chapter under these topics that's gone longest without
    being reopened -- the maintenance-mode "spaced review" pick."""
    candidates = {}
    for topic_key in topic_keys:
        group = groups.get(topic_key)
        if not group:
            continue
        for chapter in group["subgroups"]:
            if chapter["done"] < chapter["total"] or chapter["code"] in candidates:
                continue
            candidates[chapter["code"]] = {**chapter, "topic_key": topic_key}
    if not candidates:
        return None
    opened = dict(
        ChapterProgress.objects.filter(user=user, atc_code__in=candidates).values_list(
            "atc_code", "last_opened_at"
        )
    )
    return min(candidates.values(), key=lambda c: opened.get(c["code"], _NEVER))


def _maintenance_items(user, plan):
    """Always recomputed for just today -- driven by what's currently due or
    weak, which changes day to day, not a fixed curriculum to pre-schedule."""
    today = timezone.localdate()
    backlog = []

    due = due_card_count(user)
    if due:
        backlog.append({
            "activity_type": StudyPlanItem.FLASHCARDS,
            "topic_key": "",
            "atc_code": "",
            "estimated_minutes": min(20, max(5, round(due * 0.4))),
            "reason_fa": f"{due} فلش‌کارت سررسیده برای مرور داری.",
            "reason_en": f"You have {due} flashcards due for review.",
        })
    if Mistake.objects.filter(user=user, resolved=False).exists():
        backlog.append({
            "activity_type": StudyPlanItem.MISTAKE_REVIEW,
            "topic_key": "",
            "atc_code": "",
            "estimated_minutes": MISTAKE_REVIEW_MINUTES,
            "reason_fa": "هنوز اشتباهات حل‌نشده‌ای برای مرور داری.",
            "reason_en": "You still have unresolved mistakes to review.",
        })
    topic_keys = plan.topic_keys or [t["key"] for t in STUDY_TOPICS]
    stalest = _stalest_read_chapter(user, _groups_by_topic(user), topic_keys)
    if stalest:
        backlog.append({
            "activity_type": StudyPlanItem.LESSON,
            "topic_key": stalest["topic_key"],
            "atc_code": stalest["code"],
            "estimated_minutes": LESSON_MINUTES_PER_CHAPTER,
            "reason_fa": f"مدتی از آخرین مرور «{stalest['name_fa']}» گذشته.",
            "reason_en": f"It's been a while since you last reviewed {stalest['name_en']}.",
        })

    buckets, _fits = _pack_into_days(backlog, [today], plan.daily_minutes)
    return _flatten(buckets), True


def regenerate_items(user, plan):
    """Replace this plan's untouched future (today included) items with a
    freshly generated set. Anything already completed or skipped is left
    alone -- replanning must not erase history (see the planning spec's
    Replanning section)."""
    today = timezone.localdate()
    StudyPlanItem.objects.filter(
        plan=plan, day__gte=today, status=StudyPlanItem.PENDING
    ).delete()

    if plan.mode == StudyPlan.MODE_GOAL:
        rows, fits = _goal_items(user, plan)
    elif plan.mode == StudyPlan.MODE_MAINTENANCE:
        rows, fits = _maintenance_items(user, plan)
    else:
        return True

    StudyPlanItem.objects.bulk_create(StudyPlanItem(plan=plan, **row) for row in rows)
    return fits


def ensure_today_items(user, plan):
    """Maintenance plans have no pre-built schedule -- make sure today's
    pick exists before it's read."""
    if plan.mode != StudyPlan.MODE_MAINTENANCE:
        return
    today = timezone.localdate()
    if not StudyPlanItem.objects.filter(plan=plan, day=today).exists():
        regenerate_items(user, plan)


def _sync_lesson_item(item):
    """A lesson item completes itself once its chapter is actually fully
    read, however the learner got there -- studying outside the planner
    must count (see the planning spec's "manual activity affects the smart
    plan" requirement)."""
    if item.status != StudyPlanItem.PENDING or not item.atc_code:
        return item
    chapters = {c["code"]: c for c in topic_chapters(item.plan.user, item.topic_key)}
    chapter = chapters.get(item.atc_code)
    if chapter and chapter["total"] and chapter["done"] >= chapter["total"]:
        item.status = StudyPlanItem.DONE
        item.completed_at = timezone.now()
        item.save(update_fields=["status", "completed_at"])
    return item


def today_items(user, plan):
    """Today's items for the Today screen, with lesson items that turned out
    to already be fully read (studied outside the planner) synced to "done"
    first."""
    ensure_today_items(user, plan)
    today = timezone.localdate()
    items = list(plan.items.filter(day=today).order_by("order"))
    return [_sync_lesson_item(item) for item in items]


def complete_item(user, item_id):
    item = StudyPlanItem.objects.select_related("plan").get(id=item_id, plan__user=user)
    if item.status == StudyPlanItem.PENDING:
        item.status = StudyPlanItem.DONE
        item.completed_at = timezone.now()
        item.save(update_fields=["status", "completed_at"])
    return item


def skip_item(user, item_id):
    item = StudyPlanItem.objects.select_related("plan").get(id=item_id, plan__user=user)
    if item.status == StudyPlanItem.PENDING:
        item.status = StudyPlanItem.SKIPPED
        item.save(update_fields=["status"])
    return item
