from django.urls import path
from . import views

urlpatterns = [
    path("support/conversations/", views.ConversationListView.as_view()),
    path("support/conversations/<uuid:conversation_id>/messages/", views.MessageListView.as_view()),
    path("support/conversations/<uuid:conversation_id>/read/", views.ReadView.as_view()),
    path("support/summary/", views.SummaryView.as_view()),
    path("support/subscription/", views.SubscriptionView.as_view()),
]
