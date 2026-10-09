import random
from collections import defaultdict

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.lessons.data.study_topics import STUDY_TOPICS
from apps.progress.services import (
    XP_PER_CORRECT_ANSWER,
    bump_mistake,
    get_progress,
    record_quiz_answers,
    record_study,
)

from .bank_selectors import preview_selection, sample_bank_questions
from .mastery_selectors import best_score_pct_for_topic, topic_mastery_map, weak_topics_count
from .models import BankQuestion, DRUG_SESSION_CATEGORY, FIELD_META, QuizAnswer, QuizQuestion, QuizSession
from .serializers import (
    QuizAnswerInSerializer,
    QuizAnswerOutSerializer,
    QuizOverviewSerializer,
    QuizPreviewSerializer,
    QuizResultSerializer,
    QuizSessionSerializer,
    QuizStartSerializer,
)

_VALID_TOPIC_KEYS = {t["key"] for t in STUDY_TOPICS}


def _questions_from_bank(session, picked):
    return [
        QuizQuestion(
            session=session,
            order=i,
            prompt_fa=bq.prompt_fa,
            # No English bank content yet -- fall back to Persian rather
            # than show an empty question in English mode.
            prompt_en=bq.prompt_fa,
            options_fa=bq.options_fa,
            options_en=bq.options_fa,
            correct_index=bq.correct_index,
            subject_slug=bq.ingredient.slug,
            field=bq.field,
            bank_question=bq,
        )
        for i, bq in enumerate(picked)
    ]


class QuizOverviewView(APIView):
    """Everything the setup screen's stats strip and per-topic badges need,
    loaded once up front."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=QuizOverviewSerializer)
    def get(self, request):
        progress = get_progress(request.user)
        return Response({
            "avg_score_pct": progress.accuracy_pct,
            "total_quizzes": progress.total_quizzes,
            "weak_topics_count": weak_topics_count(request.user),
            "mastery": topic_mastery_map(request.user),
        })


class QuizPreviewView(APIView):
    """What a quiz of this size, on this selection, would actually cover --
    refetched as the learner changes topic / ATC chapter / count."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("category", str),
            OpenApiParameter("atc_code", str, required=False),
            OpenApiParameter("count", int),
        ],
        responses=QuizPreviewSerializer,
    )
    def get(self, request):
        category = request.query_params.get("category", "").strip()
        atc_code = request.query_params.get("atc_code", "").strip().upper()
        try:
            count = int(request.query_params.get("count", 10))
        except ValueError:
            count = 10
        if not atc_code and category not in _VALID_TOPIC_KEYS:
            raise PlatformAPIError(
                "Unknown study topic.", code="INVALID_CATEGORY", status_code=400
            )
        return Response(preview_selection(category, atc_code, count))


class QuizStartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=QuizStartSerializer, responses=QuizSessionSerializer)
    def post(self, request):
        body = QuizStartSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        ingredient_slug = body.validated_data["ingredient_slug"].strip()

        if ingredient_slug:
            # Every available question for this one drug, not a sampled
            # subset -- this is "test yourself on what you just read", not a
            # topic-scoped quiz, so category is the DRUG_SESSION_CATEGORY
            # sentinel (kept out of the per-topic mastery map) rather than a
            # study-topic key.
            picked = list(
                BankQuestion.objects.filter(ingredient__slug=ingredient_slug).select_related("ingredient")
            )
            random.shuffle(picked)
            if not picked:
                raise PlatformAPIError(
                    "No question material for this drug yet.",
                    code="INSUFFICIENT_QUESTIONS",
                    status_code=422,
                )
            category = DRUG_SESSION_CATEGORY
            atc_code = ""
            count = len(picked)
        else:
            category = body.validated_data["category"]
            atc_code = body.validated_data["atc_code"].upper()
            count = int(body.validated_data["count"])

            # Not validated against STUDY_TOPICS when atc_code is given: a
            # chapter can be reached under more than one topic, or (the
            # lesson_groups "other-<L1>" fallback) under none of the curated
            # ones, and atc_code alone is enough to resolve the question pool.
            if not atc_code and category not in _VALID_TOPIC_KEYS:
                raise PlatformAPIError(
                    "Unknown study topic.", code="INVALID_CATEGORY", status_code=400
                )

            picked = sample_bank_questions(category, atc_code, count)
            if len(picked) < count:
                raise PlatformAPIError(
                    "Not enough question material for that selection yet.",
                    code="INSUFFICIENT_QUESTIONS",
                    status_code=422,
                )

        with transaction.atomic():
            session = QuizSession.objects.create(
                user=request.user, category=category, atc_code=atc_code, question_count=count
            )
            QuizQuestion.objects.bulk_create(_questions_from_bank(session, picked[:count]))
        session.refresh_from_db()
        return Response(QuizSessionSerializer(session).data, status=201)


class QuizReviewMistakesView(APIView):
    """Starts a new session containing exactly the questions the learner
    missed in a finished one -- "مرور فقط اشتباهات" on the results screen."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=QuizSessionSerializer)
    def post(self, request, session_id):
        source = _owned_session(request.user, session_id)
        if not source.is_finished:
            raise PlatformAPIError(
                "That quiz isn't finished yet.", code="QUIZ_NOT_FINISHED", status_code=409
            )
        missed = list(
            source.questions.filter(answer__is_correct=False).order_by("order")
        )
        if not missed:
            raise PlatformAPIError(
                "No missed questions to review.", code="NOTHING_TO_REVIEW", status_code=422
            )

        with transaction.atomic():
            session = QuizSession.objects.create(
                user=request.user,
                category=source.category,
                atc_code=source.atc_code,
                question_count=len(missed),
            )
            QuizQuestion.objects.bulk_create([
                QuizQuestion(
                    session=session,
                    order=i,
                    prompt_fa=q.prompt_fa,
                    prompt_en=q.prompt_en,
                    options_fa=q.options_fa,
                    options_en=q.options_en,
                    correct_index=q.correct_index,
                    subject_slug=q.subject_slug,
                    field=q.field,
                    bank_question_id=q.bank_question_id,
                )
                for i, q in enumerate(missed)
            ])
        session.refresh_from_db()
        return Response(QuizSessionSerializer(session).data, status=201)


class QuizAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=QuizAnswerInSerializer, responses=QuizAnswerOutSerializer)
    def post(self, request, session_id):
        session = _owned_session(request.user, session_id)
        if session.is_finished:
            raise PlatformAPIError(
                "This quiz is already finished.",
                code="QUIZ_ALREADY_FINISHED",
                status_code=409,
            )

        body = QuizAnswerInSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data

        try:
            question = session.questions.get(pk=data["question_id"])
        except QuizQuestion.DoesNotExist:
            raise PlatformAPIError(
                "That question is not in this quiz.", code="INVALID_QUESTION", status_code=400
            )
        if hasattr(question, "answer"):
            raise PlatformAPIError(
                "That question is already answered.", code="ALREADY_ANSWERED", status_code=409
            )

        is_correct = data["selected_index"] == question.correct_index
        QuizAnswer.objects.create(
            question=question,
            selected_index=data["selected_index"],
            is_correct=is_correct,
            client_answered_at=data.get("client_answered_at"),
        )
        return Response({
            "correct": is_correct,
            "correct_index": question.correct_index,
            "extra_context": _extra_context(question),
        })


def _extra_context(question, limit=2):
    """1-2 more facts about the same drug and field, beyond the one this
    question already used -- the "explain more" panel's content. Empty if
    the source bank row is gone (a bank rebuild) or there's nothing else."""
    if not question.bank_question_id or not question.field:
        return []
    siblings = (
        BankQuestion.objects.filter(
            ingredient_id=question.bank_question.ingredient_id, field=question.field
        )
        .exclude(pk=question.bank_question_id)
        .order_by("id")[:limit]
    )
    return [bq.options_fa[bq.correct_index] for bq in siblings if bq.options_fa]


class QuizFinishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=QuizResultSerializer)
    def post(self, request, session_id):
        session = _owned_session(request.user, session_id)
        answers = QuizAnswer.objects.filter(question__session=session).select_related("question")
        answered = answers.count()
        score = sum(1 for a in answers if a.is_correct)

        if not session.is_finished:
            session.score = score
            session.finished_at = timezone.now()
            session.save(update_fields=["score", "finished_at"])

            record_quiz_answers(request.user, answered=answered, correct=score)
            record_study(
                request.user,
                minutes=max(1, round(session.question_count * 0.5)),
                quizzes=1,
                xp=score * XP_PER_CORRECT_ANSWER,
            )

        mistakes_added = 0
        missed = []
        field_totals = defaultdict(lambda: [0, 0])  # field -> [correct, total]
        for answer in answers:
            q = answer.question
            if q.field:
                bucket = field_totals[q.field]
                bucket[1] += 1
                if answer.is_correct:
                    bucket[0] += 1
            if answer.is_correct:
                continue
            missed.append({
                "prompt_fa": q.prompt_fa,
                "options_fa": q.options_fa,
                "correct_index": q.correct_index,
                "selected_index": answer.selected_index,
            })
            bump_mistake(
                request.user,
                topic_key="drug_class",
                topic_fa="دستهٔ دارویی",
                topic_en="Drug class",
                detail_fa="دسته‌بندی ATC داروهایی که اشتباه پاسخ دادی را مرور کن.",
                detail_en="Review the ATC class of the drugs you missed.",
            )
            mistakes_added += 1

        by_field = [
            {
                "field": field,
                "label_fa": FIELD_META.get(field, (field, "info"))[0],
                "tone": FIELD_META.get(field, (field, "info"))[1],
                "correct": correct,
                "total": total,
            }
            for field, (correct, total) in field_totals.items()
        ]

        return Response({
            "score": score,
            "total": session.question_count,
            "mistakes_added": mistakes_added,
            "by_field": by_field,
            "missed": missed,
            "previous_best_pct": best_score_pct_for_topic(
                request.user, session.category, exclude_session_id=session.id
            ),
        })


def _owned_session(user, session_id):
    try:
        return QuizSession.objects.get(pk=session_id, user=user)
    except QuizSession.DoesNotExist:
        raise PlatformAPIError("No such quiz session.", code="NOT_FOUND", status_code=404)
