from django.urls import path

from .views import (
    BoxesView,
    DeckOverviewView,
    DueCardsView,
    LeitnerCardsView,
    LeitnerOverviewView,
    LeitnerReviewView,
    ReviewView,
    SeedView,
    TopicAnswerView,
    TopicDeckView,
    TopicRestartView,
)

urlpatterns = [
    path("flashcards/leitner/", LeitnerOverviewView.as_view(), name="leitner-overview"),
    path("flashcards/leitner/cards/", LeitnerCardsView.as_view(), name="leitner-cards"),
    path("flashcards/leitner/cards/<int:pk>/review/", LeitnerReviewView.as_view(), name="leitner-review"),
    # The old per-drug box, for apps installed before the Leitner box above.
    path("flashcards/", DueCardsView.as_view(), name="flashcard-due"),
    path("flashcards/boxes/", BoxesView.as_view(), name="flashcard-boxes"),
    path("flashcards/seed/", SeedView.as_view(), name="flashcard-seed"),
    path("flashcards/<int:pk>/review/", ReviewView.as_view(), name="flashcard-review"),
    path("flashcards/decks/", DeckOverviewView.as_view(), name="flashcard-decks"),
    path("flashcards/decks/<slug:topic_key>/", TopicDeckView.as_view(), name="flashcard-deck"),
    path(
        "flashcards/decks/<slug:topic_key>/answer/",
        TopicAnswerView.as_view(),
        name="flashcard-deck-answer",
    ),
    path(
        "flashcards/decks/<slug:topic_key>/restart/",
        TopicRestartView.as_view(),
        name="flashcard-deck-restart",
    ),
]
