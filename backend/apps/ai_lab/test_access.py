from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing.models import GuestAccount
from . import access


@override_settings(
    AI_LAB_ENABLED=True,
    AI_LAB_PUBLIC_ENABLED=False,
    AI_LAB_LOCAL_LEXICAL_PILOT=False,
    AI_LAB_USER_IDS=set(),
    AI_LAB_ROLLOUT_PERCENT=0,
    AI_LAB_RELEASE_APPROVAL_FILE="",
    CACHES={name: {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                   "LOCATION": "public-access-" + name} for name in ["default", "throttle", "ai_lab"]},
)
class PublicAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("public-search-learner")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_public_access_is_opt_in_and_does_not_grant_management_roles(self):
        self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
        with override_settings(AI_LAB_PUBLIC_ENABLED=True), patch.object(access, "cohort") as cohort:
            self.assertTrue(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
            self.assertEqual(self.client.get("/api/v1/ai-lab/active/").status_code, 200)
            cohort.assert_not_called()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.role_assignments.exists())

    @override_settings(AI_LAB_PUBLIC_ENABLED=True, AI_LAB_ENABLED=False)
    def test_master_switch_still_hides_and_denies_search(self):
        self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
        response = self.client.post("/api/v1/ai-lab/ask/", {"question": "پرسش"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "AI_LAB_DISABLED")

    @override_settings(AI_LAB_PUBLIC_ENABLED=True)
    def test_public_access_requires_an_active_authenticated_registered_account(self):
        self.assertFalse(access.allowed(AnonymousUser()))
        self.user.is_active = False
        self.assertFalse(access.allowed(self.user))
        guest = get_user_model().objects.create_user("public-search-guest")
        GuestAccount.objects.create(user=guest)
        self.assertFalse(access.allowed(guest))
        self.client.force_authenticate(guest)
        self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])

    @override_settings(AI_LAB_PUBLIC_ENABLED=True, AI_LAB_LOCAL_LEXICAL_PILOT=True, ENVIRONMENT="local")
    def test_public_flag_does_not_open_the_local_lexical_pilot(self):
        self.assertFalse(access.allowed(self.user))

    def test_existing_pilot_and_admin_paths_are_preserved(self):
        with override_settings(AI_LAB_USER_IDS={str(self.user.pk)}):
            self.assertTrue(access.allowed(self.user))
        with patch.object(access, "cohort", return_value=True):
            self.assertTrue(access.allowed(self.user))
        admin = get_user_model().objects.create_user("public-search-admin", is_superuser=True)
        self.assertTrue(access.allowed(admin))
