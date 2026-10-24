from django.db.models import Count, Min, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.billing.enforcement import require_feature, require_topic_content
from apps.drugs.models import Ingredient
from apps.progress.services import XP_PER_REVIEW, record_study

from .decks import all_decks, deck_slugs, next_topic, progress_map, topic_meta
from .models import MAX_BOX, LeitnerCard, TopicProgress
from .serializers import (
    BoxSummarySerializer,
    DeckAnswerSerializer,
    DeckOverviewSerializer,
    DeckProgressSerializer,
    LeitnerCardSerializer,
    ReviewSerializer,
    TopicDeckSerializer,
)
from .services import seed_deck

DUE_PAGE_SIZE = 20


class DueCardsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeitnerCardSerializer(many=True))
    def get(self, request):
        require_feature(request, "flashcards")
        cards = (
            LeitnerCard.objects.filter(user=request.user, due_at__lte=timezone.now())
            .select_related("ingredient")
            .prefetch_related("ingredient__flashcard_facts")[:DUE_PAGE_SIZE]
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
        require_feature(request, "flashcards")
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
        require_feature(request, "flashcards", item=card.ingredient.slug, consume=True)

        body = ReviewSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        card.review(body.validated_data["rating"])
        card.save(update_fields=["box", "due_at", "times_seen", "last_reviewed_at"])

        record_study(request.user, minutes=1, reviews=1, xp=XP_PER_REVIEW)
        card.ingredient.sections.all()  # warm for serializer
        return Response(LeitnerCardSerializer(card).data)


# --- topic decks: category -> sub-category (study topic) -> its drugs ------


def _unknown_topic():
    return PlatformAPIError("No such flashcard topic.", code="NOT_FOUND", status_code=404)


def _progress_payload(progress, total, topic_key):
    position = min(progress.position, total) if progress else 0
    finished = bool(total) and position >= total
    return {
        "total": total,
        "position": position,
        "known": progress.known if progress else 0,
        "hard": progress.hard if progress else 0,
        "finished": finished,
        "next_topic": next_topic(topic_key) if finished else None,
    }


class DeckOverviewView(APIView):
    """The category grid and each category's topic list, with this learner's
    progress through every topic deck."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DeckOverviewSerializer)
    def get(self, request):
        progress = progress_map(request.user)
        categories = []
        topics_finished = 0
        cards_reviewed = 0
        for deck in all_decks():
            topics = []
            for entry in deck["topics"]:
                topic, total = entry["topic"], len(entry["slugs"])
                p = progress.get(topic["key"])
                position = min(p.position, total) if p else 0
                finished = position >= total
                topics_finished += finished
                cards_reviewed += position
                topics.append({
                    "key": topic["key"],
                    "name_fa": topic["name_fa"],
                    "name_en": topic["name_en"],
                    "total": total,
                    "position": position,
                    "finished": finished,
                })
            category = deck["category"]
            categories.append({
                "key": category["key"],
                "name_fa": category["name_fa"],
                "name_en": category["name_en"],
                "topics_finished": sum(t["finished"] for t in topics),
                "topics": topics,
            })
        return Response({
            "topics_finished": topics_finished,
            "cards_reviewed": cards_reviewed,
            "categories": categories,
        })


class TopicDeckView(APIView):
    """One topic's whole deck, in order, with where this learner is in it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TopicDeckSerializer)
    def get(self, request, topic_key):
        slugs = deck_slugs(topic_key)
        if slugs is None:
            raise _unknown_topic()
        require_feature(request, "flashcards")
        require_topic_content(request, topic_key)
        by_slug = {
            ing.slug: ing
            for ing in Ingredient.objects.filter(slug__in=slugs).prefetch_related("flashcard_facts")
        }
        topic, category = topic_meta(topic_key)
        progress = TopicProgress.objects.filter(user=request.user, topic_key=topic_key).first()
        return Response(TopicDeckSerializer({
            "key": topic["key"],
            "name_fa": topic["name_fa"],
            "name_en": topic["name_en"],
            "category_key": category["key"],
            "category_name_fa": category["name_fa"],
            "category_name_en": category["name_en"],
            "cards": [by_slug[s] for s in slugs if s in by_slug],
            **_progress_payload(progress, len(slugs), topic_key),
        }).data)


class TopicAnswerView(APIView):
    """Rate one card of a topic deck. Always updates that drug's Leitner card
    (creating it if needed), so decks feed spaced repetition; the deck itself
    advances only when the card answered is the next one in order -- going
    back over the hard cards after the deck is done doesn't move it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=DeckAnswerSerializer, responses=DeckProgressSerializer)
    def post(self, request, topic_key):
        slugs = deck_slugs(topic_key)
        if slugs is None:
            raise _unknown_topic()
        body = DeckAnswerSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        slug, rating = body.validated_data["drug_slug"], body.validated_data["rating"]
        if slug not in slugs:
            raise PlatformAPIError(
                "That drug is not in this topic's deck.", code="NOT_IN_DECK", status_code=422
            )
        require_topic_content(request, topic_key)
        require_feature(request, "flashcards", item=slug, consume=True)

        ingredient = Ingredient.objects.get(slug=slug)
        card, _ = LeitnerCard.objects.get_or_create(user=request.user, ingredient=ingredient)
        card.review(rating)
        card.save(update_fields=["box", "due_at", "times_seen", "last_reviewed_at"])
        record_study(request.user, minutes=1, reviews=1, xp=XP_PER_REVIEW)

        progress, _ = TopicProgress.objects.get_or_create(user=request.user, topic_key=topic_key)
        if progress.position < len(slugs) and slugs.index(slug) == progress.position:
            progress.position += 1
            if rating == "easy":
                progress.known += 1
            else:
                progress.hard += 1
            if progress.position >= len(slugs):
                progress.finished_at = timezone.now()
            progress.save()
        return Response(DeckProgressSerializer(_progress_payload(progress, len(slugs), topic_key)).data)


class TopicRestartView(APIView):
    """Start a topic deck over from its first drug."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=DeckProgressSerializer)
    def post(self, request, topic_key):
        slugs = deck_slugs(topic_key)
        if slugs is None:
            raise _unknown_topic()
        TopicProgress.objects.update_or_create(
            user=request.user,
            topic_key=topic_key,
            defaults={"position": 0, "known": 0, "hard": 0, "finished_at": None},
        )
        return Response(DeckProgressSerializer(_progress_payload(None, len(slugs), topic_key)).data)
