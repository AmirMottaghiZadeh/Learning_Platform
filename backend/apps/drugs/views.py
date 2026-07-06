from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, views
from rest_framework.response import Response
from .models import Drug, DrugTopic
from .serializers import DrugSerializer, DrugTopicSerializer, TargetCategorySerializer
from .services import list_target_categories

class TopicListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = DrugTopic.objects.all().order_by("id")
    serializer_class = DrugTopicSerializer

class DrugListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Drug.objects.all().order_by("id")
    serializer_class = DrugSerializer


class TargetCategoryListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=TargetCategorySerializer(many=True))
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        source_type = request.query_params.get("source_type") or ""
        categories = list_target_categories(product_id=product_id, source_type=source_type)
        return Response(TargetCategorySerializer(categories, many=True).data)
