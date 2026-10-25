from django.urls import path

from . import views

app_name = "manage"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("activity/", views.activity, name="activity"),
    path("search/", views.search, name="search"),
]
