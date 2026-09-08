from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from .models import Mistake
from .selectors import dashboard, statistics
from .serializers import (
    DashboardSerializer,
    MistakeSerializer,
    StatisticsSerializer,
    StudyPlanSerializer,
)
from .services import get_plan


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request):
        return Response(DashboardSerializer(dashboard(request.user)).data)


class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=StatisticsSerializer)
    def get(self, request):
        return Response(StatisticsSerializer(statistics(request.user)).data)


class MistakeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MistakeSerializer(many=True))
    def get(self, request):
        qs = Mistake.objects.filter(user=request.user)
        return Response(MistakeSerializer(qs, many=True).data)


class MistakeResolveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=MistakeSerializer)
    def post(self, request, mistake_id):
        try:
            mistake = Mistake.objects.get(pk=mistake_id, user=request.user)
        except Mistake.DoesNotExist:
            raise PlatformAPIError("No such mistake.", code="NOT_FOUND", status_code=404)
        if not mistake.resolved:
            mistake.resolved = True
            mistake.save(update_fields=["resolved", "last_seen"])
        return Response(MistakeSerializer(mistake).data)


class MistakeRestoreView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=MistakeSerializer(many=True))
    def post(self, request):
        Mistake.objects.filter(user=request.user, resolved=True).update(resolved=False)
        qs = Mistake.objects.filter(user=request.user)
        return Response(MistakeSerializer(qs, many=True).data)


class StudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=StudyPlanSerializer)
    def get(self, request):
        return Response(StudyPlanSerializer(get_plan(request.user)).data)

    @extend_schema(request=StudyPlanSerializer, responses=StudyPlanSerializer)
    def put(self, request):
        plan = get_plan(request.user)
        serializer = StudyPlanSerializer(plan, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
