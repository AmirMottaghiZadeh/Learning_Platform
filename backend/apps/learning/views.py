from drf_spectacular.utils import extend_schema
from rest_framework import generics, views
from rest_framework.response import Response

from .models import LearnerProgress
from .selectors import (
    get_learning_dashboard,
    get_learning_progress_summary,
    get_learning_recommendations,
    get_learning_statistics,
    progress_queryset_for_user,
)
from .serializers import (
    LearnerProgressSerializer,
    LearningDashboardSerializer,
    LearningProgressSummarySerializer,
    LearningStatisticsSerializer,
    RecommendationSerializer,
)


class LearningProgressSummaryView(views.APIView):
    @extend_schema(responses=LearningProgressSummarySerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or None
        summary = get_learning_progress_summary(request.user, product_id=product_id)
        return Response(LearningProgressSummarySerializer(summary).data)


class LearnerProgressListView(generics.ListAPIView):
    serializer_class = LearnerProgressSerializer

    def get_queryset(self):
        product_id = self.request.query_params.get("product_id") or None
        return progress_queryset_for_user(self.request.user, product_id=product_id)


class LearningDashboardView(views.APIView):
    @extend_schema(responses=LearningDashboardSerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        dashboard = get_learning_dashboard(request.user, product_id=product_id)
        return Response(LearningDashboardSerializer(dashboard).data)


class LearningRecommendationView(views.APIView):
    @extend_schema(responses=RecommendationSerializer(many=True))
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        recommendations = get_learning_recommendations(request.user, product_id=product_id)
        return Response(RecommendationSerializer(recommendations, many=True).data)


class LearningStatisticsView(views.APIView):
    @extend_schema(responses=LearningStatisticsSerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        statistics = get_learning_statistics(request.user, product_id=product_id)
        return Response(LearningStatisticsSerializer(statistics).data)
