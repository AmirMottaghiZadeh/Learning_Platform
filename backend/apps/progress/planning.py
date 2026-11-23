"""Study-plan generation and topic mastery.

Deliberately separate from `services.py` (which just records what already
happened) and `selectors.py` (which just reads): this module *decides* what a
learner should study next, so its logic -- the mastery formula, the
generation algorithm, replanning -- stays out of both the views and the other
apps that feed it signals (lessons/quiz).

Three planning models share this one module because they share the same
underlying signals (`ReadDrug`, quiz answers) -- see
`models.StudyPlan` for what distinguishes "goal" from "maintenance".
"""

from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Max
from django.utils import timezone

from apps.drugs.data.atc_reference import ATC_L2
from apps.lessons.data.study_topics import CATEGORIES, STUDY_TOPICS
from apps.lessons.models import ChapterProgress
from apps.lessons.selectors import l2_slug_index, lesson_groups, read_slugs_for_user, slugs_for_topic, topic_progress
from apps.quiz.models import BankQuestion, COUNT_CHOICES, QuizAnswer, QuizSession

from .models import DailyStudy, Mistake, StudyPlan, StudyPlanItem
from .services import get_plan

LESSON_MINUTES_PER_CHAPTER = 10
# The learner's onboarding level sets the pace: the minutes a chapter is
# planned at, so a beginner gets fewer new chapters a day than an advanced
# learner with the same daily time.
LESSON_MINUTES_BY_LEVEL = {"beginner": 14, "intermediate": 10, "advanced": 7}
# An open-ended daily review (the "clinical" onboarding goal) by default.
MAINTENANCE_DEFAULT_MINUTES = 10
QUIZ_MINUTES = 10
CHAPTER_QUIZ_COUNT = min(COUNT_CHOICES)
CHAPTER_QUIZ_MINUTES = 5
MISTAKE_REVIEW_MINUTES = 10

# Assessment accuracy and reading completion are renormalised over the
# signals available for this learner. Before the first quiz only completion
# contributes; the ratio between completion and quiz remains 3:4.
MASTERY_WEIGHTS = {"completion": 0.3, "quiz": 0.4}

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


def topic_mastery(user, topic_key):
    """0-100: how well the learner actually knows this topic, as distinct
    from how much of it they've merely read (see `topic_progress` for that)."""
    slugs = slugs_for_topic(topic_key)
    signals = {"completion": topic_progress(user, topic_key)["pct"]}
    quiz_pct = _quiz_accuracy_for_slugs(user, slugs)
    if quiz_pct is not None:
        signals["quiz"] = quiz_pct
    total_weight = sum(MASTERY_WEIGHTS[k] for k in signals)
    return round(sum(v * MASTERY_WEIGHTS[k] for k, v in signals.items()) / total_weight)


# -- generation -------------------------------------------------------------


def _groups_by_topic(user):
    """`lesson_groups(user)` rebuilds its ingredient index from scratch, so
    every generation call fetches it exactly once and the topic loops below
    share that one result instead of re-querying per topic."""
    return {g["code"]: g for g in lesson_groups(user)}


def _lesson_minutes(user):
    profile = getattr(user, "learner_profile", None)
    return LESSON_MINUTES_BY_LEVEL.get(getattr(profile, "study_level", ""), LESSON_MINUTES_PER_CHAPTER)


def _topic_backlog(topic_key, group, lesson_minutes=LESSON_MINUTES_PER_CHAPTER, done=frozenset(),
                   done_chapters=frozenset()):
    """Ordered work units for one topic: unread chapters first, then one
    quiz over the whole topic -- left out
    once `done` (pairs of topic key and activity) says it was done, and a
    chapter left out once the learner ticked its task off (`done_chapters`),
    read or not."""
    topic = _topic_by_key(topic_key)
    if not topic:
        return []
    chapters = _with_chapters(group)
    items = []
    for chapter in chapters["unread"]:
        if chapter["code"] in done_chapters:
            continue
        items.append({
            "activity_type": StudyPlanItem.LESSON,
            "topic_key": topic_key,
            "atc_code": chapter["code"],
            "estimated_minutes": lesson_minutes,
            "reason_fa": f"هنوز فصل «{chapter['name_fa']}» را نخوانده‌ای.",
            "reason_en": f"You haven't read the {chapter['name_en']} chapter yet.",
        })
    if chapters["all"] and (topic_key, StudyPlanItem.QUIZ) not in done:
        items.append({
            "activity_type": StudyPlanItem.QUIZ,
            "topic_key": topic_key,
            "atc_code": "",
            "estimated_minutes": QUIZ_MINUTES,
            "reason_fa": f"یک آزمون کوتاه برای سنجش تسلطت روی «{topic['name_fa']}».",
            "reason_en": f"A short quiz to check your grasp of {topic['name_en']}.",
        })
    return items


def _weekday_index(d):
    """`date.weekday()` is Mon=0..Sun=6; `StudyPlan.days` is Sat=0..Fri=6."""
    return (d.weekday() + 2) % 7


def _study_days(days, start, end):
    """Calendar dates in [start, end] whose weekday is enabled in `days`."""
    out = []
    d = start
    while d <= end:
        if days[_weekday_index(d)]:
            out.append(d)
        d += timedelta(days=1)
    return out


def _pack_into_days(backlog, study_days, daily_minutes, used=None):
    """Greedily fills each study day up to `daily_minutes` before spilling
    into the next one. A single item longer than the daily budget still
    gets placed (as the only thing that day) rather than blocking forever.
    `used` holds minutes a day already has (today's finished tasks, when
    replanning). `study_days` is never empty -- callers always fall back
    to [today]."""
    buckets = {d: [] for d in study_days}
    minutes_used = {d: (used or {}).get(d, 0) for d in study_days}
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


def _atc_chapters(user, groups):
    index = l2_slug_index()
    read = read_slugs_for_user(user)
    return {
        group: [{"code": code, "slugs": slugs, "total": len(slugs), "done": len(read.intersection(slugs)),
                 "name_en": ATC_L2.get(code, (code, code))[0], "name_fa": ATC_L2.get(code, (code, code))[1]}
                for code, slugs in sorted(index.items()) if code.startswith(group)]
        for group in groups
    }


def atc_schedule(user, settings, plan=None):
    """Build the same ordered, bounded schedule for preview, save and rollover."""
    groups = _atc_chapters(user, settings["atc_groups"])
    today = timezone.localdate()
    chapters = [chapter for items in groups.values() for chapter in items]
    slugs = {slug for chapter in chapters for slug in chapter["slugs"]}
    question_counts = dict(BankQuestion.objects.filter(ingredient__slug__in=slugs)
                           .values("ingredient__slug").annotate(count=Count("pk")).values_list("ingredient__slug", "count"))
    quiz_chapters = set(QuizSession.objects.filter(user=user, finished_at__isnull=False,
                                                  atc_code__in=[chapter["code"] for chapter in chapters])
                        .values_list("atc_code", flat=True))
    finished = set(plan.items.filter(status=StudyPlanItem.DONE).values_list("activity_type", "atc_code")) if plan else set()
    backlog = []
    missing_quizzes = 0
    for chapter in chapters:
        code = chapter["code"]
        common = {"topic_key": code[0], "atc_code": code}
        if chapter["done"] < chapter["total"] and (StudyPlanItem.LESSON, code) not in finished:
            backlog.append({**common, "activity_type": StudyPlanItem.LESSON, "estimated_minutes": LESSON_MINUTES_PER_CHAPTER,
                            "reason_fa": "این فصل هنوز کامل مطالعه نشده است.", "reason_en": "This chapter has unread material."})
        if code in quiz_chapters or (StudyPlanItem.QUIZ, code) in finished:
            continue
        if sum(question_counts.get(slug, 0) for slug in chapter["slugs"]) < CHAPTER_QUIZ_COUNT:
            missing_quizzes += 1
            continue
        backlog.append({**common, "activity_type": StudyPlanItem.QUIZ, "estimated_minutes": CHAPTER_QUIZ_MINUTES,
                        "reason_fa": "آزمون کوتاه از همان فصل دارونامه.", "reason_en": "A short quiz on the same chapter."})

    natural_end = today + timedelta(weeks=len(backlog) + 1)
    deadline = settings.get("deadline")
    days = _study_days(settings["days"], today, min(deadline, natural_end) if deadline else natural_end)
    used_today = sum(plan.items.filter(day=today).exclude(status=StudyPlanItem.PENDING)
                     .values_list("estimated_minutes", flat=True)) if plan else 0
    buckets, fits = _pack_into_days(backlog, days, settings["daily_minutes"], used={today: used_today})
    rows = _flatten(buckets)
    first = rows[0] if rows else None
    first_activity = None
    if first:
        chapter_en, chapter_fa = ATC_L2.get(first["atc_code"], (first["atc_code"], first["atc_code"]))
        first_activity = {"atc_code": first["atc_code"], "activity_type": first["activity_type"],
                          "day": first["day"], "name_fa": chapter_fa, "name_en": chapter_en}
    summary = {"fits_deadline": fits, "chapter_count": len(chapters), "missing_quiz_count": missing_quizzes,
               "remaining_minutes": sum(item["estimated_minutes"] for item in backlog),
               "study_sessions": len({row["day"] for row in rows}), "first_activity": first_activity,
               "estimated_finish": rows[-1]["day"] if rows and fits else None,
               "empty_groups": [group for group, items in groups.items() if not items]}
    return rows, summary


def save_atc_plan(user, settings):
    """Called inside a transaction. Invalid estimates leave the old plan intact."""
    from rest_framework.exceptions import ValidationError

    plan = StudyPlan.objects.select_for_update().get(pk=get_plan(user).pk)
    rows, summary = atc_schedule(user, settings, plan)
    if not summary["chapter_count"]:
        raise ValidationError({"atc_groups": "برای گروه‌های انتخابی هنوز فصلی در دسترس نیست."})
    if not summary["fits_deadline"]:
        raise ValidationError({"deadline": "زمان تا آزمون برای این برنامه کافی نیست."})
    if (plan.atc_groups, plan.deadline) != (settings["atc_groups"], settings.get("deadline")) or not plan.started_on:
        plan.started_on = timezone.localdate()
    plan.mode = StudyPlan.MODE_GOAL
    plan.atc_groups = settings["atc_groups"]
    plan.topic_keys = []
    plan.deadline = settings.get("deadline")
    plan.days = settings["days"]
    plan.daily_minutes = settings["daily_minutes"]
    plan.reminders_enabled = False
    plan.rolled_over_on = None
    plan.save()
    _replace_pending_items(plan, rows)
    return plan


def _goal_items(user, plan):
    if plan.atc_groups:
        rows, summary = atc_schedule(user, {"atc_groups": plan.atc_groups, "days": plan.days,
                                           "deadline": plan.deadline, "daily_minutes": plan.daily_minutes}, plan)
        return rows, summary["fits_deadline"]
    groups = _groups_by_topic(user)
    done = set(
        plan.items.filter(
            status=StudyPlanItem.DONE, activity_type=StudyPlanItem.QUIZ
        ).values_list("topic_key", "activity_type")
    )
    done_chapters = set(
        plan.items.filter(status=StudyPlanItem.DONE, activity_type=StudyPlanItem.LESSON).values_list("atc_code", flat=True)
    )
    lesson_minutes = _lesson_minutes(user)
    backlog = []
    for topic_key in plan.topic_keys:
        backlog.extend(_topic_backlog(topic_key, groups.get(topic_key), lesson_minutes, done, done_chapters))

    today = timezone.localdate()
    end = max(plan.deadline or today, today)
    study_days = _study_days(plan.days, today, end) or [today]
    # What today already holds (finished or skipped tasks survive replanning)
    # counts against today's time.
    used_today = sum(plan.items.filter(day=today).exclude(status=StudyPlanItem.PENDING).values_list("estimated_minutes", flat=True))
    buckets, fits = _pack_into_days(backlog, study_days, plan.daily_minutes, used={today: used_today})
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
    if not plan.days[_weekday_index(today)]:
        return [], True
    backlog = []

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
    if plan.mode == StudyPlan.MODE_GOAL:
        rows, fits = _goal_items(user, plan)
    elif plan.mode == StudyPlan.MODE_MAINTENANCE:
        rows, fits = _maintenance_items(user, plan)
    else:
        _delete_pending_items(plan)
        return True
    _replace_pending_items(plan, rows)
    return fits


def _delete_pending_items(plan):
    plan.items.filter(day__gte=timezone.localdate(), status=StudyPlanItem.PENDING).delete()


def _replace_pending_items(plan, rows):
    _delete_pending_items(plan)
    today = timezone.localdate()
    # Today's new tasks follow the ones already finished there.
    last_order = plan.items.filter(day=today).aggregate(last=Max("order"))["last"]
    kept_today = 0 if last_order is None else last_order + 1
    for row in rows:
        if row["day"] == today:
            row["order"] += kept_today
    StudyPlanItem.objects.bulk_create(StudyPlanItem(plan=plan, **row) for row in rows)


@transaction.atomic
def rollover(user, plan):
    """A goal plan whose study day passed with tasks left: the remaining work
    is laid out again from today, at most once a day, so it moves onto the
    coming study days instead of piling up behind. The missed day's tasks
    stay as they were -- the week shows that day as missed."""
    if plan.mode != StudyPlan.MODE_GOAL or (not plan.deadline and not plan.atc_groups):
        return
    today = timezone.localdate()
    if plan.rolled_over_on == today or (plan.deadline and plan.deadline < today):
        return
    plan = StudyPlan.objects.select_for_update().get(pk=plan.pk)
    if plan.rolled_over_on == today or plan.mode != StudyPlan.MODE_GOAL:
        return
    if plan.items.filter(day__lt=today, status=StudyPlanItem.PENDING).exists():
        regenerate_items(user, plan)
    plan.rolled_over_on = today
    plan.save(update_fields=["rolled_over_on"])


def plan_from_onboarding(user, goal, *, exam_date, daily_minutes, days, category_keys):
    """The study plan the onboarding answers make (accounts' OnboardingSerializer):
    an end-of-course exam plans every topic up to the exam, term finals only
    the topics of the chosen categories, and daily clinical review is an
    open-ended maintenance plan."""
    plan = get_plan(user)
    plan.atc_groups = []
    if goal == "clinical":
        plan.mode = StudyPlan.MODE_MAINTENANCE
        plan.topic_keys = []
        plan.deadline = None
        plan.daily_minutes = daily_minutes or MAINTENANCE_DEFAULT_MINUTES
    else:
        plan.mode = StudyPlan.MODE_GOAL
        categories = set(category_keys) if goal == "final" else {c["key"] for c in CATEGORIES}
        plan.topic_keys = [t["key"] for t in STUDY_TOPICS if t["category"] in categories]
        plan.deadline = exam_date
        plan.daily_minutes = daily_minutes
    plan.days = days
    plan.started_on = timezone.localdate()
    plan.rolled_over_on = None
    plan.save()
    regenerate_items(user, plan)
    return plan


def ensure_today_items(user, plan):
    """Maintenance plans have no pre-built schedule -- make sure today's
    pick exists before it's read. Respects the plan's own chosen study days,
    same as goal mode, rather than nagging on an off day."""
    if plan.mode != StudyPlan.MODE_MAINTENANCE:
        return
    today = timezone.localdate()
    if not plan.days[_weekday_index(today)]:
        return
    if not StudyPlanItem.objects.filter(plan=plan, day=today).exists():
        regenerate_items(user, plan)


def _chapter(groups, item):
    group = groups.get(item.topic_key)
    return next((c for c in (group["subgroups"] if group else []) if c["code"] == item.atc_code), None)


def _is_done_elsewhere(user, item, groups):
    """Whether the learner already did this task outside the planner --
    studying the normal way must count (the planning spec's "manual
    activity affects the smart plan" requirement):
    - a lesson: its chapter is fully read;
    - a quiz: a quiz on its topic was finished that day or later;
    - a mistake review: no mistake is left open."""
    if item.activity_type == StudyPlanItem.LESSON:
        chapter = _chapter(groups, item) if item.atc_code else None
        return bool(chapter and chapter["total"] and chapter["done"] >= chapter["total"])
    if item.activity_type == StudyPlanItem.QUIZ:
        if item.atc_code:
            return QuizSession.objects.filter(user=user, atc_code=item.atc_code, finished_at__isnull=False).exists()
        return bool(item.topic_key) and QuizSession.objects.filter(
            user=user, category=item.topic_key, finished_at__date__gte=item.day
        ).exists()
    if item.activity_type == StudyPlanItem.MISTAKE_REVIEW:
        return not Mistake.objects.filter(user=user, resolved=False).exists()
    return False


def _title(item, groups):
    """What the task is, for the Today box: "Formulary: Antihypertensives"."""
    topic = _topic_by_key(item.topic_key)
    topic_fa, topic_en = (topic["name_fa"], topic["name_en"]) if topic else ("", "")
    if item.activity_type == StudyPlanItem.LESSON:
        chapter = _chapter(groups, item)
        return (f"دارونامه: {chapter['name_fa'] if chapter else topic_fa}",
                f"Formulary: {chapter['name_en'] if chapter else topic_en}")
    if item.activity_type == StudyPlanItem.QUIZ:
        if item.atc_code:
            chapter_en, chapter_fa = ATC_L2.get(item.atc_code, (item.atc_code, item.atc_code))
            return f"آزمون: {chapter_fa}", f"Quiz: {chapter_en}"
        return f"آزمون: {topic_fa}", f"Quiz: {topic_en}"
    return "مرور اشتباه‌ها", "Review your mistakes"


def today_items(user, plan):
    """Today's items for the Today box, each with its title and with tasks
    already done outside the planner synced to "done" first."""
    rollover(user, plan)
    ensure_today_items(user, plan)
    today = timezone.localdate()
    items = list(plan.items.filter(day=today).order_by("order"))
    if items and plan.atc_groups:
        groups = {key: {"subgroups": chapters} for key, chapters in _atc_chapters(user, plan.atc_groups).items()}
    else:
        groups = _groups_by_topic(user) if items else {}
    for item in items:
        if item.status == StudyPlanItem.PENDING and _is_done_elsewhere(user, item, groups):
            item.status = StudyPlanItem.DONE
            item.completed_at = timezone.now()
            item.save(update_fields=["status", "completed_at"])
        item.title_fa, item.title_en = _title(item, groups)
    return items


def week_overview(user, plan):
    """This week, Saturday to Friday, one entry a day: "done" (every task
    finished, or -- with no tasks laid out -- some study recorded), "missed"
    (a study day gone by with tasks left), "today", "planned" (a study day
    to come), "free" (not a study day) or "off" (before the plan began)."""
    today = timezone.localdate()
    start = today - timedelta(days=_weekday_index(today))
    days = [start + timedelta(days=i) for i in range(7)]
    tasks = defaultdict(lambda: {"total": 0, "pending": 0})
    for day, status in plan.items.filter(day__gte=days[0], day__lte=days[-1]).values_list("day", "status"):
        tasks[day]["total"] += 1
        tasks[day]["pending"] += status == StudyPlanItem.PENDING
    studied = set(
        DailyStudy.objects.filter(user=user, day__in=days, minutes__gt=0).values_list("day", flat=True)
    )
    began = plan.started_on or (plan.updated_at.date() if plan.updated_at else today)
    week = []
    for i, day in enumerate(days):
        study_day = bool(plan.days[i])
        task = tasks.get(day)
        if task and task["total"] and not task["pending"]:
            state = "done"
        elif day == today:
            state = "today" if study_day or task else "free"
        elif day > today:
            state = "planned" if study_day else "free"
        elif not study_day:
            state = "free"
        elif day < began:
            state = "off"
        elif not task and day in studied:
            state = "done"
        else:
            state = "missed"
        week.append({"date": day, "study_day": study_day, "state": state})
    return week


def plan_summary(plan):
    """The line above the Today box: days to the exam, "week 2 of 6" and how
    much of the plan is done. A missed task that was laid out again counts
    once, by its new copy."""
    today = timezone.localdate()
    summary = {
        "daily_minutes": plan.daily_minutes,
        "study_days": sum(1 for d in plan.days if d),
        "deadline": plan.deadline,
        "days_left": None,
        "week_index": None,
        "week_count": None,
        "progress_pct": None,
    }
    if plan.mode != StudyPlan.MODE_GOAL or (not plan.deadline and not plan.atc_groups):
        return summary
    began = plan.started_on or (plan.updated_at.date() if plan.updated_at else today)
    estimated_end = plan.deadline or plan.items.filter(day__gte=today).order_by("-day").values_list("day", flat=True).first() or today
    week_count = max(1, (estimated_end - began).days // 7 + 1)
    done = plan.items.filter(status=StudyPlanItem.DONE).count()
    left = plan.items.filter(status=StudyPlanItem.PENDING, day__gte=today).count()
    summary.update({
        "days_left": max(0, (plan.deadline - today).days) if plan.deadline else None,
        "week_index": min(week_count, max(1, (today - began).days // 7 + 1)),
        "week_count": week_count,
        "progress_pct": round(100 * done / (done + left)) if done + left else 0,
    })
    return summary


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
