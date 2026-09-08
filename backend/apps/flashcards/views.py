from django.db.models import Count, Min, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.progress.services import XP_PER_REVIEW, record_study

from .models import MAX_BOX, LeitnerCard
from .serializers import (
    BoxSummarySerializer,
    LeitnerCardSerializer,
    ReviewSerializer,
)
from .services import seed_deck

DUE_PAGE_SIZE = 20


class DueCardsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeitnerCardSerializer(many=True))
    def get(self, request):
        cards = (
            LeitnerCard.objects.filter(user=request.user, due_at__lte=timezone.now())
            .select_related("ingredient")
            .prefetch_related("ingredient__sections")[:DUE_PAGE_SIZE]
        )
        return Response(LeitnerCardSerializer(cards, many=True).data)


class BoxesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=BoxSummarySerializer(many=True))
    def get(self, request):
        now = timezone.now()
        rows = {
            r["box"]: r
            for r in LeitnerCard.objects.filter(user=request.user)
            .values("box")
            .annotate(
                count=Count("id"),
                due=Count("id", filter=Q(due_at__lte=now)),
                next_due_at=Min("due_at"),
            )
        }
        summary = [
            {
                "box": b,
                "count": rows.get(b, {}).get("count", 0),
                "due": rows.get(b, {}).get("due", 0),
                "next_due_at": rows.get(b, {}).get("next_due_at"),
            }
            for b in range(1, MAX_BOX + 1)
        ]
        return Response(BoxSummarySerializer(summary, many=True).data)


class SeedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=BoxSummarySerializer)
    def post(self, request):
        result = seed_deck(request.user)
        return Response(result, status=201 if result["created"] else 200)


class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ReviewSerializer, responses=LeitnerCardSerializer)
    def post(self, request, pk):
        try:
            card = LeitnerCard.objects.select_related("ingredient").get(pk=pk, user=request.user)
        except LeitnerCard.DoesNotExist:
            raise PlatformAPIError("No such card.", code="NOT_FOUND", status_code=404)

        body = ReviewSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        card.review(body.validated_data["rating"])
        card.save(update_fields=["box", "due_at", "times_seen", "last_reviewed_at"])

        record_study(request.user, minutes=1, reviews=1, xp=XP_PER_REVIEW)
        card.ingredient.sections.all()  # warm for serializer
        return Response(LeitnerCardSerializer(card).data)
