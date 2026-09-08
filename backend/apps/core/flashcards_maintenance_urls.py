from django.urls import path

from .maintenance_urls import maintenance_response


urlpatterns = [
    path("flashcards/", maintenance_response),
    path("flashcards/boxes/", maintenance_response),
    path("flashcards/decks/", maintenance_response),
    path("flashcards/seed/", maintenance_response),
    path("flashcards/<int:pk>/review/", maintenance_response),
]
