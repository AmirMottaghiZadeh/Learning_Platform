from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.lessons.data.study_topics import STUDY_TOPICS
from apps.lessons.selectors import topic_progress

from . import planning
from .models import Mistake, StudyPlanItem
from .selectors import dashboard, statistics
from .serializers import (
    DashboardSerializer,
    MistakeSerializer,
    PlanTodaySerializer,
    StatisticsSerializer,
    StudyPlanItemSerializer,
    StudyPlanSaveResponseSerializer,
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

    @extend_schema(request=StudyPlanSerializer, responses=StudyPlanSaveResponseSerializer)
    def put(self, request):
        plan = get_plan(request.user)
        serializer = StudyPlanSerializer(plan, data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        fits = planning.regenerate_items(request.user, plan)
        return Response({**serializer.data, "fits_deadline": fits})


class PlanTodayView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=PlanTodaySerializer)
    def get(self, request):
        plan = get_plan(request.user)
        items = planning.today_items(request.user, plan)
        topics = [
            {
                "key": topic["key"],
                "name_fa": topic["name_fa"],
                "name_en": topic["name_en"],
                "progress_pct": topic_progress(request.user, topic["key"])["pct"],
                "mastery_pct": planning.topic_mastery(request.user, topic["key"]),
            }
            for topic in STUDY_TOPICS
            if topic["key"] in plan.topic_keys
        ]
        return Response(
            PlanTodaySerializer({
                "mode": plan.mode,
                "items": items,
                "total_minutes": sum(item.estimated_minutes for item in items),
                "topics": topics,
            }).data
        )


class PlanItemCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=StudyPlanItemSerializer)
    def post(self, request, item_id):
        try:
            item = planning.complete_item(request.user, item_id)
        except StudyPlanItem.DoesNotExist:
            raise PlatformAPIError("No such plan item.", code="NOT_FOUND", status_code=404)
        return Response(StudyPlanItemSerializer(item).data)


class PlanItemSkipView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=StudyPlanItemSerializer)
    def post(self, request, item_id):
        try:
            item = planning.skip_item(request.user, item_id)
        except StudyPlanItem.DoesNotExist:
            raise PlatformAPIError("No such plan item.", code="NOT_FOUND", status_code=404)
        return Response(StudyPlanItemSerializer(item).data)
