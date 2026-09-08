from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    LogoutAllView,
    MeView,
    OnboardingView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshSessionView,
    RegisterView,
    RoleAssignmentListCreateView,
    RoleAssignmentRevokeView,
    RoleListView,
    SecurityAuditListView,
    SessionListView,
    SessionRevokeView,
    StepUpView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshSessionView.as_view(), name="auth-refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("logout-all/", LogoutAllView.as_view(), name="auth-logout-all"),
    path("sessions/", SessionListView.as_view(), name="auth-session-list"),
    path(
        "sessions/<uuid:session_id>/revoke/",
        SessionRevokeView.as_view(),
        name="auth-session-revoke",
    ),
    path("step-up/", StepUpView.as_view(), name="auth-step-up"),
    path("roles/", RoleListView.as_view(), name="auth-role-list"),
    path(
        "role-assignments/",
        RoleAssignmentListCreateView.as_view(),
        name="auth-role-assignment-list",
    ),
    path(
        "role-assignments/<int:assignment_id>/revoke/",
        RoleAssignmentRevokeView.as_view(),
        name="auth-role-assignment-revoke",
    ),
    path(
        "security-events/",
        SecurityAuditListView.as_view(),
        name="auth-security-event-list",
    ),
    path("me/", MeView.as_view(), name="auth-me"),
    path("onboarding/", OnboardingView.as_view(), name="auth-onboarding"),
]
