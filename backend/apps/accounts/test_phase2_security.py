from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Role,
    RoleAssignment,
    SecurityAuditEvent,
    SessionRefreshToken,
    UserSession,
)
from .services import hash_session_token, issue_user_session


class PhaseTwoSessionSecurityTests(TestCase):
    password = "Saffron-River-Atlas-2026!"

    def setUp(self):
        cache.clear()
        caches["throttle"].clear()
        self.user = get_user_model().objects.create_user(
            username="phase-two-user",
            email="phase-two@example.com",
            password=self.password,
        )

    def tearDown(self):
        cache.clear()
        caches["throttle"].clear()
        super().tearDown()

    def bearer(self, access_token):
        return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    def test_login_issues_only_hashed_tokens_and_records_audit_metadata(self):
        response = self.client.post(
            reverse("auth-login"),
            {
                "username": self.user.username,
                "password": self.password,
                "device_name": "Firefox on Linux",
            },
            content_type="application/json",
            HTTP_USER_AGENT="Phase2 Test Agent",
            REMOTE_ADDR="203.0.113.7",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        session = UserSession.objects.get(id=payload["session_id"])
        self.assertEqual(payload["token_type"], "Bearer")
        self.assertEqual(
            session.access_token_hash,
            hash_session_token(payload["access_token"]),
        )
        self.assertEqual(
            session.refresh_token_hash,
            hash_session_token(payload["refresh_token"]),
        )
        self.assertNotEqual(session.access_token_hash, payload["access_token"])
        self.assertNotEqual(session.refresh_token_hash, payload["refresh_token"])
        self.assertEqual(session.device_name, "Firefox on Linux")
        self.assertEqual(session.user_agent, "Phase2 Test Agent")
        self.assertEqual(str(session.ip_address), "203.0.113.7")
        event = SecurityAuditEvent.objects.get(
            event_type=SecurityAuditEvent.LOGIN_SUCCEEDED,
            session=session,
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.ip_address, "203.0.113.7")

    def test_failed_login_is_audited(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": "wrong-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        event = SecurityAuditEvent.objects.get(
            event_type=SecurityAuditEvent.LOGIN_FAILED
        )
        self.assertEqual(event.metadata["username"], self.user.username)

    def test_multi_device_inventory_marks_only_current_session(self):
        first = issue_user_session(self.user, device_name="Laptop")
        second = issue_user_session(self.user, device_name="Phone")

        response = self.client.get(
            reverse("auth-session-list"),
            **self.bearer(first.access_token),
        )

        self.assertEqual(response.status_code, 200)
        sessions = {item["device_name"]: item for item in response.json()}
        self.assertEqual(set(sessions), {"Laptop", "Phone"})
        self.assertTrue(sessions["Laptop"]["current"])
        self.assertFalse(sessions["Phone"]["current"])
        self.assertEqual(
            UserSession.objects.filter(user=self.user, revoked_at__isnull=True).count(),
            2,
        )

    def test_expired_access_is_rejected_while_refresh_can_rotate_session(self):
        issued = issue_user_session(self.user)
        now = timezone.now()
        UserSession.objects.filter(id=issued.session.id).update(
            created_at=now - timedelta(hours=1),
            access_expires_at=now - timedelta(seconds=1),
        )

        response = self.client.get(
            reverse("auth-me"),
            **self.bearer(issued.access_token),
        )
        refresh_response = self.client.post(
            reverse("auth-refresh"),
            {"refresh_token": issued.refresh_token},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(refresh_response.status_code, 200)
        self.assertNotEqual(
            refresh_response.json()["access_token"],
            issued.access_token,
        )

    def test_refresh_rotation_invalidates_old_refresh_and_detects_reuse(self):
        issued = issue_user_session(self.user)
        refresh_response = self.client.post(
            reverse("auth-refresh"),
            {"refresh_token": issued.refresh_token},
            content_type="application/json",
        )

        self.assertEqual(refresh_response.status_code, 200)
        rotated = refresh_response.json()
        self.assertNotEqual(rotated["refresh_token"], issued.refresh_token)
        old_token = SessionRefreshToken.objects.get(
            token_hash=hash_session_token(issued.refresh_token)
        )
        self.assertIsNotNone(old_token.used_at)
        self.assertEqual(
            old_token.replaced_by_hash,
            hash_session_token(rotated["refresh_token"]),
        )

        reuse_response = self.client.post(
            reverse("auth-refresh"),
            {"refresh_token": issued.refresh_token},
            content_type="application/json",
        )

        self.assertEqual(reuse_response.status_code, 401)
        issued.session.refresh_from_db()
        self.assertIsNotNone(issued.session.revoked_at)
        self.assertEqual(issued.session.revoke_reason, "refresh_token_reuse")

    def test_logout_revokes_only_current_device(self):
        laptop = issue_user_session(self.user, device_name="Laptop")
        phone = issue_user_session(self.user, device_name="Phone")

        response = self.client.post(
            reverse("auth-logout"),
            {},
            content_type="application/json",
            **self.bearer(laptop.access_token),
        )

        self.assertEqual(response.status_code, 204)
        laptop.session.refresh_from_db()
        phone.session.refresh_from_db()
        self.assertIsNotNone(laptop.session.revoked_at)
        self.assertIsNone(phone.session.revoked_at)

    def test_device_revoke_and_logout_all(self):
        current = issue_user_session(self.user, device_name="Laptop")
        other = issue_user_session(self.user, device_name="Phone")

        revoke_response = self.client.post(
            reverse("auth-session-revoke", args=[other.session.id]),
            {"reason": "lost_device"},
            content_type="application/json",
            **self.bearer(current.access_token),
        )
        self.assertEqual(revoke_response.status_code, 204)
        other.session.refresh_from_db()
        self.assertEqual(other.session.revoke_reason, "lost_device")

        replacement = issue_user_session(self.user, device_name="Tablet")
        logout_all_response = self.client.post(
            reverse("auth-logout-all"),
            {},
            content_type="application/json",
            **self.bearer(current.access_token),
        )
        self.assertEqual(logout_all_response.status_code, 204)
        current.session.refresh_from_db()
        replacement.session.refresh_from_db()
        self.assertIsNotNone(current.session.revoked_at)
        self.assertIsNotNone(replacement.session.revoked_at)

    @override_settings(AUTH_MAX_ACTIVE_SESSIONS=2)
    def test_session_cap_revokes_the_oldest_device(self):
        first = issue_user_session(self.user, device_name="First")
        second = issue_user_session(self.user, device_name="Second")
        third = issue_user_session(self.user, device_name="Third")

        first.session.refresh_from_db()
        second.session.refresh_from_db()
        third.session.refresh_from_db()
        self.assertEqual(first.session.revoke_reason, "session_limit")
        self.assertIsNone(second.session.revoked_at)
        self.assertIsNone(third.session.revoked_at)


class PhaseTwoAuthorizationTests(TestCase):
    password = "Saffron-River-Atlas-2026!"

    def setUp(self):
        self.actor = get_user_model().objects.create_user(
            username="role-admin",
            email="role-admin@example.com",
            password=self.password,
        )
        self.target = get_user_model().objects.create_user(
            username="role-target",
            email="role-target@example.com",
            password=self.password,
        )
        RoleAssignment.objects.create(
            user=self.actor,
            role=Role.objects.get(key=Role.PLATFORM_ADMIN),
        )
        self.issued = issue_user_session(self.actor)

    def bearer(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.issued.access_token}"}

    def test_role_mutation_requires_recent_step_up_and_is_audited(self):
        role_payload = {
            "user_id": self.target.id,
            "role": Role.DATA_QUALITY_REVIEWER,
            "reason": "Operational review duty",
        }
        denied = self.client.post(
            reverse("auth-role-assignment-list"),
            role_payload,
            content_type="application/json",
            **self.bearer(),
        )
        self.assertEqual(denied.status_code, 403)
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                event_type=SecurityAuditEvent.AUTHORIZATION_DENIED,
                metadata__reason="step_up_required",
            ).exists()
        )

        failed_step_up = self.client.post(
            reverse("auth-step-up"),
            {"password": "wrong-password"},
            content_type="application/json",
            **self.bearer(),
        )
        self.assertEqual(failed_step_up.status_code, 403)

        step_up = self.client.post(
            reverse("auth-step-up"),
            {"password": self.password},
            content_type="application/json",
            **self.bearer(),
        )
        self.assertEqual(step_up.status_code, 204)
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                event_type=SecurityAuditEvent.STEP_UP_VERIFIED,
                session=self.issued.session,
            ).exists()
        )

        assigned = self.client.post(
            reverse("auth-role-assignment-list"),
            role_payload,
            content_type="application/json",
            **self.bearer(),
        )
        self.assertEqual(assigned.status_code, 201)
        assignment = RoleAssignment.objects.get(
            user=self.target,
            role__key=Role.DATA_QUALITY_REVIEWER,
            revoked_at__isnull=True,
        )
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                event_type=SecurityAuditEvent.ROLE_ASSIGNED,
                user=self.target,
                actor=self.actor,
            ).exists()
        )

        revoked = self.client.post(
            reverse("auth-role-assignment-revoke", args=[assignment.id]),
            {"reason": "Duty completed"},
            content_type="application/json",
            **self.bearer(),
        )
        self.assertEqual(revoked.status_code, 200)
        assignment.refresh_from_db()
        self.assertIsNotNone(assignment.revoked_at)

    def test_role_and_security_inventory_require_granular_permissions(self):
        role_response = self.client.get(
            reverse("auth-role-list"),
            **self.bearer(),
        )
        audit_response = self.client.get(
            reverse("auth-security-event-list"),
            **self.bearer(),
        )
        self.assertEqual(role_response.status_code, 200)
        self.assertEqual(audit_response.status_code, 200)

        unprivileged = issue_user_session(self.target)
        denied = self.client.get(
            reverse("auth-security-event-list"),
            HTTP_AUTHORIZATION=f"Bearer {unprivileged.access_token}",
        )
        self.assertEqual(denied.status_code, 403)
