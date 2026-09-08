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
