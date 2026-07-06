from django.urls import path
from .views import (
    FlashcardBoxSummaryView,
    FlashcardDeckSummaryView,
    FlashcardListView,
    FlashcardReviewView,
    FlashcardSeedView,
)

urlpatterns = [
    path("flashcards/", FlashcardListView.as_view()),
    path("flashcards/boxes/", FlashcardBoxSummaryView.as_view()),
    path("flashcards/decks/", FlashcardDeckSummaryView.as_view()),
    path("flashcards/seed/", FlashcardSeedView.as_view()),
    path("flashcards/<int:pk>/review/", FlashcardReviewView.as_view()),
]
