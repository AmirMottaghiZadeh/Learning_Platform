from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.progress.services import (
    XP_PER_CORRECT_ANSWER,
    bump_mistake,
    record_quiz_answers,
    record_study,
)

from .generator import generate_questions
from .models import QuizAnswer, QuizQuestion, QuizSession
from .serializers import (
    QuizAnswerInSerializer,
    QuizAnswerOutSerializer,
    QuizResultSerializer,
    QuizSessionSerializer,
    QuizStartSerializer,
)


class QuizStartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=QuizStartSerializer, responses=QuizSessionSerializer)
    def post(self, request):
        body = QuizStartSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        category = body.validated_data["category"]
        count = int(body.validated_data["count"])

        generated = generate_questions(category, count)
        if len(generated) < count:
            raise PlatformAPIError(
                "Not enough question material for that category yet.",
                code="INSUFFICIENT_QUESTIONS",
                status_code=422,
            )

        with transaction.atomic():
            session = QuizSession.objects.create(
                user=request.user, category=category, question_count=count
            )
            QuizQuestion.objects.bulk_create([
                QuizQuestion(session=session, order=i, **q)
                for i, q in enumerate(generated[:count])
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
        return Response({"correct": is_correct, "correct_index": question.correct_index})


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
        for answer in answers:
            if answer.is_correct:
                continue
            bump_mistake(
                request.user,
                topic_key="drug_class",
                topic_fa="دستهٔ دارویی",
                topic_en="Drug class",
                detail_fa="دسته‌بندی ATC داروهایی که اشتباه پاسخ دادی را مرور کن.",
                detail_en="Review the ATC class of the drugs you missed.",
            )
            mistakes_added += 1

        return Response({
            "score": score,
            "total": session.question_count,
            "mistakes_added": mistakes_added,
        })


def _owned_session(user, session_id):
    try:
        return QuizSession.objects.get(pk=session_id, user=user)
    except QuizSession.DoesNotExist:
        raise PlatformAPIError("No such quiz session.", code="NOT_FOUND", status_code=404)
