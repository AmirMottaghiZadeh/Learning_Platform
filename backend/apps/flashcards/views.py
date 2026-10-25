from django.db.models import Count, Min, Q, prefetch_related_objects
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.billing.enforcement import require_feature, require_topic_content
from apps.drugs.models import Ingredient
from apps.progress.services import XP_PER_REVIEW, record_study

from . import leitner
from .decks import all_decks, deck_cards, next_topic, progress_map, topic_meta
from .models import MAX_BOX, LeitnerCard, TopicProgress
from .serializers import (
    BoxCardSerializer,
    BoxReviewSerializer,
    BoxSummarySerializer,
    DeckAnswerSerializer,
    DeckOverviewSerializer,
    DeckProgressSerializer,
    LeitnerCardSerializer,
    LeitnerOverviewSerializer,
    ReviewSerializer,
    TopicDeckSerializer,
)
from .services import seed_deck

DUE_PAGE_SIZE = 20


# --- the old box: per-drug cards, kept answering apps installed before the
# Leitner box below replaced it. They only ever see cards with no section.


class DueCardsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeitnerCardSerializer(many=True))
    def get(self, request):
        require_feature(request, "flashcards")
        cards = (
            LeitnerCard.objects.filter(user=request.user, section="", due_at__lte=timezone.now())
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
            for r in LeitnerCard.objects.filter(user=request.user, section="")
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
            card = LeitnerCard.objects.select_related("ingredient").get(pk=pk, user=request.user, section="")
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
                topic, total = entry["topic"], len(entry["cards"])
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
        cards = deck_cards(topic_key)
        if cards is None:
            raise _unknown_topic()
        require_feature(request, "flashcards")
        require_topic_content(request, topic_key)
        by_slug = {
            ing.slug: ing
            for ing in Ingredient.objects.filter(slug__in={slug for slug, _ in cards}).prefetch_related("flashcard_facts")
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
            "cards": [{"ingredient": by_slug[slug], "section": section} for slug, section in cards if slug in by_slug],
            **_progress_payload(progress, len(cards), topic_key),
        }).data)


class TopicAnswerView(APIView):
    """Rate one card of a topic deck. "hard" -- "یادم نبود" -- puts that card
    in the Leitner box (or a drawer up), so only what the learner did not
    know is reviewed there; the deck itself advances only when the card
    answered is the next one in order -- going back over the hard cards
    after the deck is done doesn't move it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=DeckAnswerSerializer, responses=DeckProgressSerializer)
    def post(self, request, topic_key):
        cards = deck_cards(topic_key)
        if cards is None:
            raise _unknown_topic()
        body = DeckAnswerSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        slug, rating = body.validated_data["drug_slug"], body.validated_data["rating"]
        progress, _ = TopicProgress.objects.get_or_create(user=request.user, topic_key=topic_key)
        section = body.validated_data.get("section")
        if not section:
            # An app from before one-section cards: the deck's current card
            # when it is this drug's, else the drug's first card.
            at = cards[progress.position] if progress.position < len(cards) else None
            section = at[1] if at and at[0] == slug else next((s for d, s in cards if d == slug), "")
        if (slug, section) not in cards:
            raise PlatformAPIError(
                "That card is not in this topic's deck.", code="NOT_IN_DECK", status_code=422
            )
        require_topic_content(request, topic_key)
        require_feature(request, "flashcards", item=slug, consume=True)

        if rating == "hard":
            leitner.add_miss(request.user, Ingredient.objects.get(slug=slug), section)
        record_study(request.user, minutes=1, reviews=1, xp=XP_PER_REVIEW)

        if progress.position < len(cards) and cards.index((slug, section)) == progress.position:
            progress.position += 1
            if rating == "easy":
                progress.known += 1
            else:
                progress.hard += 1
            if progress.position >= len(cards):
                progress.finished_at = timezone.now()
            progress.save()
        return Response(DeckProgressSerializer(_progress_payload(progress, len(cards), topic_key)).data)


class TopicRestartView(APIView):
    """Start a topic deck over from its first card."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=DeckProgressSerializer)
    def post(self, request, topic_key):
        cards = deck_cards(topic_key)
        if cards is None:
            raise _unknown_topic()
        TopicProgress.objects.update_or_create(
            user=request.user,
            topic_key=topic_key,
            defaults={"position": 0, "known": 0, "hard": 0, "finished_at": None},
        )
        return Response(DeckProgressSerializer(_progress_payload(None, len(cards), topic_key)).data)


# --- the Leitner box: only what the learner did not know (apps.flashcards.leitner)


def _box_cards(request, cards):
    return BoxCardSerializer(cards, many=True, context={"previews": leitner.previews(request.user, cards)}).data


def _with_facts(cards):
    """Prefetch each card's drug facts, for the card backs."""
    prefetch_related_objects(cards, "ingredient__flashcard_facts")
    return cards


class LeitnerOverviewView(APIView):
    """The five drawers (cards and how many are due in each) and today's
    review: its size within the day's minutes, with its first cards."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LeitnerOverviewSerializer)
    def get(self, request):
        require_feature(request, "flashcards")
        data = leitner.overview(request.user)
        preview = _with_facts(data["preview"])
        return Response(
            LeitnerOverviewSerializer(data, context={"previews": leitner.previews(request.user, preview)}).data
        )


class LeitnerCardsView(APIView):
    """Today's review -- due cards, highest drawer first, within the day's
    minutes -- or, with ?box=N, every card in that drawer, due or not. Each
    card carries what each review button would do to it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter("box", int, description="One drawer, 1-5, instead of today's review.")],
        responses=BoxCardSerializer(many=True),
    )
    def get(self, request):
        require_feature(request, "flashcards")
        box = request.query_params.get("box")
        if box is not None:
            if box not in {str(b) for b in range(1, MAX_BOX + 1)}:
                raise PlatformAPIError("No such drawer.", code="INVALID_BOX", status_code=400)
            cards = leitner.drawer_cards(request.user, int(box))
        else:
            cards, _due, _budget = leitner.today_queue(request.user)
        return Response(_box_cards(request, _with_facts(cards)))


class LeitnerReviewView(APIView):
    """Rate a card in the box -- forgot, hard or good -- and reschedule it.
    The answer is the card as it now is (box 0: it left the box)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=BoxReviewSerializer, responses=BoxCardSerializer)
    def post(self, request, pk):
        try:
            card = LeitnerCard.objects.in_box().select_related("ingredient").get(pk=pk, user=request.user)
        except LeitnerCard.DoesNotExist:
            raise PlatformAPIError("No such card in the box.", code="NOT_FOUND", status_code=404)
        body = BoxReviewSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        require_feature(request, "flashcards", item=card.ingredient.slug, consume=True)
        leitner.review(request.user, card, body.validated_data["rating"])
        record_study(request.user, minutes=1, reviews=1, xp=XP_PER_REVIEW)
        return Response(_box_cards(request, _with_facts([card]))[0])
