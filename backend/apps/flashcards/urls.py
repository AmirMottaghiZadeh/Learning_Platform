from django.urls import path

from .views import BoxesView, DueCardsView, ReviewView, SeedView

urlpatterns = [
    path("flashcards/", DueCardsView.as_view(), name="flashcard-due"),
    path("flashcards/boxes/", BoxesView.as_view(), name="flashcard-boxes"),
    path("flashcards/seed/", SeedView.as_view(), name="flashcard-seed"),
    path("flashcards/<int:pk>/review/", ReviewView.as_view(), name="flashcard-review"),
]
