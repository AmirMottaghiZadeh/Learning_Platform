from django.urls import path

from . import views

app_name = "data_quality_center"

urlpatterns = [
    path("", views.queue, name="queue"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("mine/", views.my_requests, name="mine"),
    path("review/", views.review_desk, name="review"),
    path("review/<int:pk>/", views.review_action, name="review_action"),
    path("history/", views.history, name="history"),
    path("edits/<int:pk>/revert/", views.revert, name="revert"),
    path("drugs/<slug:slug>/", views.workspace, name="workspace"),
    path("drugs/<slug:slug>/<str:field>/draft/", views.save_draft, name="save_draft"),
    path("drugs/<slug:slug>/<str:field>/submit/", views.submit, name="submit"),
    path("drugs/<slug:slug>/<str:field>/withdraw/", views.withdraw, name="withdraw"),
    path("drugs/<slug:slug>/<str:field>/discard/", views.discard, name="discard"),
]
