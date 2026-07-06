from drf_spectacular.utils import extend_schema
from rest_framework import generics, views, status
from rest_framework.response import Response

from apps.core.exceptions import PlatformAPIError

from .models import GameSession, Mistake
from .serializers import (
    StartGameSerializer,
    GameSessionSerializer,
    AnswerSerializer,
    GameAnswerSerializer,
    GameAnswerResultSerializer,
    GameLifecycleSerializer,
    MistakeSerializer,
)
from .services import (
    answer_question,
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
