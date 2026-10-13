import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Role(models.Model):
    LEARNER = "learner"
    VERIFIED_PROFESSIONAL = "verified_professional"
    CONTENT_EDITOR = "content_editor"
    MEDICAL_REVIEWER = "medical_reviewer"
    DATA_QUALITY_REVIEWER = "data_quality_reviewer"
    DATA_QUALITY_APPROVER = "data_quality_approver"
    SUPPORT_AGENT = "support_agent"
    BILLING_ADMIN = "billing_admin"
    PLATFORM_ADMIN = "platform_admin"

    key = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="platform_roles",
    )
    is_system = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class RoleAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_assignments_created",
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_assignments_revoked",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(revoked_at__isnull=True),
                name="unique_active_user_role",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(expires_at__isnull=True)
                    | models.Q(expires_at__gt=models.F("created_at"))
                ),
                name="role_assignment_expiry_after_creation",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "revoked_at", "expires_at"],
                name="accounts_role_user_active_idx",
            ),
        ]

    @property
    def is_active(self):
        now = timezone.now()
        return (
            self.revoked_at is None
            and (self.expires_at is None or self.expires_at > now)
        )


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_sessions",
    )
    access_token_hash = models.CharField(max_length=64, unique=True)
    refresh_token_hash = models.CharField(max_length=64, unique=True)
    access_expires_at = models.DateTimeField()
    refresh_expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField()
    step_up_verified_at = models.DateTimeField(null=True, blank=True)
    refresh_rotated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=120, blank=True)
    device_name = models.CharField(max_length=120, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(access_expires_at__gt=models.F("created_at")),
                name="session_access_expiry_after_creation",
            ),
            models.CheckConstraint(
                condition=models.Q(refresh_expires_at__gt=models.F("access_expires_at")),
                name="session_refresh_expiry_after_access",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "revoked_at", "refresh_expires_at"],
                name="acct_session_user_active_idx",
            ),
            models.Index(
                fields=["user", "-last_used_at"],
                name="acct_session_user_used_idx",
            ),
        ]

    @property
    def is_active(self):
        return self.revoked_at is None and self.refresh_expires_at > timezone.now()


class SessionRefreshToken(models.Model):
    session = models.ForeignKey(
        UserSession,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    issued_at = models.DateTimeField(default=timezone.now)
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    replaced_by_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-issued_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("issued_at")),
                name="refresh_expiry_after_issue",
            ),
        ]
        indexes = [
            models.Index(
                fields=["session", "-issued_at"],
                name="accounts_refresh_session_idx",
            ),
        ]


class LearnerProfile(models.Model):
    """Per-user learning preferences captured at onboarding.

    Separate from auth.User so onboarding answers and display name evolve
    without touching the identity model.
    """

    FIELD_CHOICES = [
        ("pharmacy", "Pharmacy"),
        ("medicine", "Medicine"),
        ("nursing", "Nursing"),
    ]
    # Onboarding offers pharmacy/medicine and comprehensive/final/clinical;
    # "nursing" and "residency" stay valid for profiles saved before that.
    GOAL_CHOICES = [
        ("comprehensive", "End-of-course exam"),
        ("residency", "Residency exam"),
        ("final", "Term finals"),
        ("clinical", "Daily clinical review"),
    ]
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    study_field = models.CharField(max_length=20, choices=FIELD_CHOICES, blank=True)
    study_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, blank=True)
    study_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True)
    language = models.CharField(max_length=5, default="fa")
    # The account's mobile number, "09xxxxxxxxx" -- set only once proven
    # with an SMS code (sign-up), so it is always a verified number. Null for
    # accounts made with an email before phone sign-up existed.
    phone = models.CharField(max_length=11, null=True, blank=True, unique=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    onboarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"LearnerProfile<{self.user_id}>"

    @property
    def is_onboarded(self):
        return self.onboarded_at is not None


class SecurityAuditEvent(models.Model):
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    SESSION_REFRESHED = "session_refreshed"
    STEP_UP_VERIFIED = "step_up_verified"
    SESSION_REVOKED = "session_revoked"
    ALL_SESSIONS_REVOKED = "all_sessions_revoked"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    AUTHORIZATION_DENIED = "authorization_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    OTP_SENT = "otp_sent"
    OTP_VERIFIED = "otp_verified"
    OTP_FAILED = "otp_failed"
    PASSWORD_SET = "password_set"

    event_type = models.CharField(max_length=80)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_actions",
    )
    session = models.ForeignKey(
        UserSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    request_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        permissions = [
            ("view_raw_drug_data", "Can view raw drug data"),
            ("view_data_quality_center", "Can view the data quality center"),
            (
                "review_data_quality_suggestion",
                "Can review data quality suggestions",
            ),
            (
                "approve_data_quality_suggestion",
                "Can approve data quality suggestions",
            ),
            ("apply_data_quality_change", "Can apply data quality changes"),
            ("manage_drug_records", "Can manage drug records"),
            ("view_security_audit", "Can view security audit events"),
            ("manage_platform_roles", "Can manage platform roles"),
        ]
        indexes = [
            models.Index(
                fields=["user", "event_type", "-occurred_at"],
                name="accounts_audit_user_event_idx",
            ),
            models.Index(
                fields=["event_type", "-occurred_at"],
                name="accounts_audit_event_time_idx",
            ),
        ]

    def __str__(self):
        return self.event_type


class OneTimeCode(models.Model):
    """One SMS code sent to a mobile number: for signing up (and signing in
    for the first time), or for resetting a forgotten password. Only an HMAC
    of the code is stored; it expires, allows a few wrong tries, and is
    spent by its first correct use (see apps.accounts.otp)."""

    SIGNUP = "signup"
    RESET = "reset"
    PURPOSE_CHOICES = [(SIGNUP, "Sign up"), (RESET, "Password reset")]

    phone = models.CharField(max_length=11)
    purpose = models.CharField(max_length=16, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # The SMS provider's id for the message, for tracing a delivery problem.
    provider_message_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "purpose", "-created_at"], name="accounts_otp_phone_idx"),
            models.Index(fields=["-created_at"], name="accounts_otp_recent_idx"),
        ]

    def __str__(self):
        return f"OneTimeCode<{self.purpose} {self.phone[:4]}…>"
