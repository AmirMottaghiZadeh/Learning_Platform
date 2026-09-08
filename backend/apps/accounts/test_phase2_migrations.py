from unittest import skipUnless

from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


@skipUnless(
    connection.vendor == "postgresql",
    "Phase 2 identity upgrade verification requires PostgreSQL.",
)
class PhaseTwoMigrationUpgradeTests(TransactionTestCase):
    reset_sequences = True

    migrate_from = [
        ("accounts", "0002_profile_names"),
        ("authtoken", "0004_alter_tokenproxy_options"),
    ]
    migrate_to = [("accounts", "0003_phase2_identity_sessions_rbac")]

    def test_legacy_identity_data_is_normalized_and_secured(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        fixture = self._create_legacy_fixture(old_apps)

        try:
            executor = MigrationExecutor(connection)
            executor.migrate(self.migrate_to)
            new_apps = executor.loader.project_state(self.migrate_to).apps
            self._assert_upgraded_state(new_apps, fixture)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def _create_legacy_fixture(self, apps):
        User = apps.get_model("auth", "User")
        Profile = apps.get_model("accounts", "Profile")
        Token = apps.get_model("authtoken", "Token")

        learner = User.objects.create(
            username="phase2-legacy-learner",
            email=" Legacy.User@Example.COM ",
        )
        admin = User.objects.create(
            username="phase2-legacy-admin",
            email="ADMIN@EXAMPLE.COM",
            is_staff=True,
            is_superuser=True,
        )
        Profile.objects.create(
            user=learner,
            username=learner.username,
            first_name="Legacy",
            last_name="Learner",
        )
        Profile.objects.create(
            user=admin,
            username=admin.username,
            first_name="Legacy",
            last_name="Admin",
        )
        Token.objects.create(key="a" * 40, user=learner)
        Token.objects.create(key="b" * 40, user=admin)
        return {"learner_id": learner.id, "admin_id": admin.id}

    def _assert_upgraded_state(self, apps, fixture):
        User = apps.get_model("auth", "User")
        Token = apps.get_model("authtoken", "Token")
        Permission = apps.get_model("auth", "Permission")
        Role = apps.get_model("accounts", "Role")
        RoleAssignment = apps.get_model("accounts", "RoleAssignment")

        with self.assertRaises(LookupError):
            apps.get_model("accounts", "Profile")
        self.assertEqual(Token.objects.count(), 0)
        self.assertEqual(
            User.objects.get(id=fixture["learner_id"]).email,
            "legacy.user@example.com",
        )
        self.assertEqual(
            User.objects.get(id=fixture["admin_id"]).email,
            "admin@example.com",
        )
        self.assertEqual(Role.objects.count(), 9)
        self.assertEqual(
            Permission.objects.filter(
                content_type__app_label="accounts",
                content_type__model="securityauditevent",
                codename__in=[
                    "view_raw_drug_data",
                    "view_data_quality_center",
                    "review_data_quality_suggestion",
                    "approve_data_quality_suggestion",
                    "apply_data_quality_change",
                    "manage_drug_records",
                    "view_security_audit",
                    "manage_platform_roles",
                ],
            ).count(),
            8,
        )
        self.assertTrue(
            RoleAssignment.objects.filter(
                user_id=fixture["learner_id"],
                role__key="learner",
                revoked_at__isnull=True,
            ).exists()
        )
        self.assertTrue(
            RoleAssignment.objects.filter(
                user_id=fixture["admin_id"],
                role__key="platform_admin",
                revoked_at__isnull=True,
            ).exists()
        )
        with self.assertRaises(IntegrityError):
            User.objects.create(
                username="phase2-duplicate-email",
                email="LEGACY.USER@EXAMPLE.COM",
            )
