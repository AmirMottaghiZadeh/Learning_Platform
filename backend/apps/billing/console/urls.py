from django.urls import path

from . import views

app_name = "console"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("users/", views.users, name="users"),
    path("users/export.csv", views.users_export, name="users_export"),
    path("users/<int:pk>/", views.user_detail, name="user"),
    path("users/<int:pk>/grant/", views.user_grant, name="user_grant"),
    path("users/<int:pk>/access/<int:eid>/extend/", views.entitlement_extend, name="entitlement_extend"),
    path("users/<int:pk>/access/<int:eid>/revoke/", views.entitlement_revoke, name="entitlement_revoke"),
    path("users/<int:pk>/block/", views.user_block, name="user_block"),
    path("users/<int:pk>/logout-all/", views.user_logout_all, name="user_logout_all"),
    path("users/<int:pk>/role/", views.user_role, name="user_role"),
    path("plans/", views.plans, name="plans"),
    path("plans/new/", views.plan_new, name="plan_new"),
    path("plans/<int:pk>/", views.plan_basics, name="plan_basics"),
    path("plans/<int:pk>/features/", views.plan_features, name="plan_features"),
    path("plans/<int:pk>/prices/", views.plan_prices, name="plan_prices"),
    path("plans/<int:pk>/review/", views.plan_review, name="plan_review"),
    path("plans/<int:pk>/copy/", views.plan_copy, name="plan_copy"),
    path("features/", views.features, name="features"),
    path("features/new/", views.feature_new, name="feature_new"),
    path("features/<int:pk>/", views.feature_edit, name="feature_edit"),
    path("discounts/", views.discounts, name="discounts"),
    path("discounts/<int:pk>/toggle/", views.discount_toggle, name="discount_toggle"),
    path("sales/", views.sales, name="sales"),
    path("audit/", views.audit, name="audit"),
]
