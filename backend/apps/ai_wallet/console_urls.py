from django.urls import path
from . import console

app_name = "ai_wallet_admin"
urlpatterns = [
    path("",console.dashboard,name="dashboard"),
    path("rate/refresh/",console.refresh_rate,name="refresh_rate"),
    path("packages/new/",console.package_edit,name="package_new"),
    path("packages/<int:pk>/",console.package_edit,name="package"),
    path("users/<int:pk>/",console.user_wallet,name="user"),
    path("review/<uuid:pk>/",console.review,name="review"),
]
