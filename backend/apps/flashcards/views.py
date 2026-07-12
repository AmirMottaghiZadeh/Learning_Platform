from drf_spectacular.utils import extend_schema
from rest_framework import generics, views
from rest_framework.response import Response
from .models import FlashcardState
from .serializers import (
    FlashcardBoxSummarySerializer,
    FlashcardDeckSummarySerializer,
    FlashcardReviewRequestSerializer,
    FlashcardSeedRequestSerializer,
    FlashcardStateSerializer,
)
from .services import get_flashcard_deck_summary, get_leitner_box_counts, review_card, seed_flashcards_for_user

class FlashcardListView(generics.ListAPIView):
    serializer_class = FlashcardStateSerializer

    def get_queryset(self):
        queryset = (
            FlashcardState.objects
            .filter(user=self.request.user)
            .select_related("knowledge_source", "source")
        )
        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(knowledge_source__product_id=product_id)
        exclude_ids = [
            int(value)
            for value in self.request.query_params.get("exclude_ids", "").split(",")
            if value.isdigit()
        ]
        if exclude_ids:
            queryset = queryset.exclude(id__in=exclude_ids)
        mode = self.request.query_params.get("mode") or "new"
        if mode == "leitner":
            return (
                queryset
                .filter(box__gte=1)
                .exclude(review_state=FlashcardState.REVIEW_STATE_SUSPENDED)
                .order_by("box", "last_reviewed_at", "id")
            )

        queryset = queryset.filter(
            box=0,
            review_state=FlashcardState.REVIEW_STATE_NEW,
        )
        target_category_key = self.request.query_params.get("target_category_key")
        if target_category_key:
            queryset = queryset.filter(
                knowledge_source__metadata__target_category_key=target_category_key
            )
        source_type = self.request.query_params.get("source_type")
        if source_type:
            queryset = queryset.filter(knowledge_source__source_type=source_type)
        return queryset.order_by("id")

class FlashcardReviewView(views.APIView):
    @extend_schema(request=FlashcardReviewRequestSerializer, responses=FlashcardStateSerializer)
    def post(self, request, pk):
        state = FlashcardState.objects.get(pk=pk, user=request.user)
        serializer = FlashcardReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review_card(state, serializer.validated_data["rating"])
        return Response(FlashcardStateSerializer(state).data)


class FlashcardSeedView(views.APIView):
    @extend_schema(request=FlashcardSeedRequestSerializer, responses=FlashcardStateSerializer(many=True))
    def post(self, request):
        serializer = FlashcardSeedRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        states = seed_flashcards_for_user(
            user=request.user,
            product_id=serializer.validated_data["product_id"],
            target_category_key=serializer.validated_data["target_category_key"],
            source_type=serializer.validated_data["source_type"],
        )
        return Response(FlashcardStateSerializer(states, many=True).data)


class FlashcardBoxSummaryView(views.APIView):
    @extend_schema(responses=FlashcardBoxSummarySerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "pharmexa"
        counts = get_leitner_box_counts(
            user=request.user,
            product_id=product_id,
        )
        return Response(FlashcardBoxSummarySerializer(counts).data)


class FlashcardDeckSummaryView(views.APIView):
    @extend_schema(responses=FlashcardDeckSummarySerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "pharmexa"
        target_category_key = request.query_params.get("target_category_key") or ""
        source_type = request.query_params.get("source_type") or ""
        summary = get_flashcard_deck_summary(
            user=request.user,
            product_id=product_id,
            target_category_key=target_category_key,
            source_type=source_type,
        )
        return Response(FlashcardDeckSummarySerializer(summary).data)
