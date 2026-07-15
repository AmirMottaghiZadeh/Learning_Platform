from drf_spectacular.utils import extend_schema
from rest_framework import generics, views, status
from rest_framework.response import Response

from apps.core.exceptions import PlatformAPIError

from .models import GameSession, Mistake, QuizReminder
from .selectors import get_quiz_history_queryset
from .serializers import (
    StartGameSerializer,
    GameSessionSerializer,
    AnswerSerializer,
    GameAnswerSerializer,
    GameAnswerResultSerializer,
    GameLifecycleSerializer,
    MistakeSerializer,
    QuizHistorySessionSerializer,
    QuizReminderCreateSerializer,
    QuizReminderSerializer,
    QuizReminderUpdateSerializer,
)
from .services import (
    answer_question,
    create_quiz_reminder,
    extend_current_question_timer,
    finish_game,
    pause_game,
    resume_game,
    start_game,
)


class GameCreateView(views.APIView):
    @extend_schema(request=StartGameSerializer, responses={201: GameSessionSerializer})
    def post(self, request):
        serializer = StartGameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            session = start_game(request.user, **serializer.validated_data)
        except ValueError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_GAME_START",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return Response(GameSessionSerializer(session).data, status=201)


class GameDetailView(generics.RetrieveAPIView):
    serializer_class = GameSessionSerializer

    def get_queryset(self):
        return GameSession.objects.filter(user=self.request.user)


class GameAnswerView(views.APIView):
    @extend_schema(request=AnswerSerializer, responses=GameAnswerResultSerializer)
    def post(self, request, pk):
        session = GameSession.objects.get(pk=pk, user=request.user)

        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            answer = answer_question(
                request.user,
                session,
                **serializer.validated_data,
            )
        except ValueError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_GAME_STATE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "answer": GameAnswerSerializer(answer).data,
                "game": GameSessionSerializer(session).data,
            }
        )

class GameFinishView(views.APIView):
    @extend_schema(request=None, responses=GameSessionSerializer)
    def post(self, request, pk):
        session = GameSession.objects.get(pk=pk, user=request.user)
        finish_game(session)
        return Response(GameSessionSerializer(session).data)


class GamePauseView(views.APIView):
    @extend_schema(request=None, responses=GameLifecycleSerializer)
    def post(self, request, pk):
        session = GameSession.objects.get(pk=pk, user=request.user)
        try:
            session = pause_game(session)
        except ValueError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_GAME_STATE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"game": GameSessionSerializer(session).data})


class GameResumeView(views.APIView):
    @extend_schema(request=None, responses=GameLifecycleSerializer)
    def post(self, request, pk):
        session = GameSession.objects.get(pk=pk, user=request.user)
        try:
            session = resume_game(session)
        except ValueError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_GAME_STATE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"game": GameSessionSerializer(session).data})


class GameExtendTimerView(views.APIView):
    @extend_schema(request=None, responses=GameLifecycleSerializer)
    def post(self, request, pk):
        session = GameSession.objects.get(pk=pk, user=request.user)
        try:
            extend_current_question_timer(session)
        except ValueError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_TIMER_EXTENSION",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"game": GameSessionSerializer(session).data})


class MyMistakesView(generics.ListAPIView):
    serializer_class = MistakeSerializer

    def get_queryset(self):
        return (
            Mistake.objects
            .filter(user=self.request.user)
            .select_related("knowledge_source", "source")
            .order_by("-wrong_count", "-last_at")
        )


class QuizReminderListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizReminderSerializer

    def get_queryset(self):
        return QuizReminder.objects.filter(user=self.request.user).order_by("is_reviewed", "-created_at")

    @extend_schema(request=QuizReminderCreateSerializer, responses={201: QuizReminderSerializer})
    def post(self, request, *args, **kwargs):
        serializer = QuizReminderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reminder = create_quiz_reminder(user=request.user, **serializer.validated_data)
        return Response(QuizReminderSerializer(reminder).data, status=status.HTTP_201_CREATED)


class QuizReminderDetailView(views.APIView):
    @extend_schema(request=QuizReminderUpdateSerializer, responses=QuizReminderSerializer)
    def patch(self, request, pk):
        reminder = QuizReminder.objects.get(pk=pk, user=request.user)
        serializer = QuizReminderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reminder.is_reviewed = serializer.validated_data["is_reviewed"]
        reminder.save(update_fields=["is_reviewed", "updated_at"])
        return Response(QuizReminderSerializer(reminder).data)


class QuizHistoryView(generics.ListAPIView):
    serializer_class = QuizHistorySessionSerializer

    def get_queryset(self):
        return get_quiz_history_queryset(user=self.request.user)
