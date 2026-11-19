from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase

from .models import Feature, Plan, PlanFeature


class SmartSearchMigrationTests(TestCase):
    def seed(self):
        migration = import_module("apps.billing.migrations.0014_smart_search_feature")
        migration.seed(apps, SimpleNamespace(connection=connection))

    def test_initial_creation_keeps_existing_free_plan_features_and_paid_plans(self):
        Feature.objects.filter(key="smart_search").delete()
        free = Plan.objects.get(is_free=True)
        free.plan_features.exclude(feature__key="lessons").delete()
        paid = Plan.objects.create(slug="existing-paid", name_fa="اشتراک موجود")
        self.seed()
        feature = Feature.objects.get(key="smart_search")
        self.assertEqual(feature.kind, Feature.KIND_BUILTIN)
        self.assertFalse(feature.countable)
        self.assertEqual(set(free.features.values_list("key", flat=True)), {"lessons", "smart_search"})
        self.assertFalse(paid.plan_features.exists())

    def test_existing_operator_configuration_is_preserved_and_seed_is_idempotent(self):
        feature = Feature.objects.get(key="smart_search")
        feature.name_fa = "نام انتخابی مدیر"
        feature.kind = Feature.KIND_CUSTOM
        feature.is_active = False
        feature.save()
        feature.plan_features.all().delete()
        for _ in range(2):
            self.seed()
        feature.refresh_from_db()
        self.assertEqual(feature.name_fa, "نام انتخابی مدیر")
        self.assertFalse(feature.is_active)
        self.assertEqual(feature.kind, Feature.KIND_BUILTIN)
        self.assertFalse(feature.plan_features.exists())
        self.assertEqual(Feature.objects.filter(key="smart_search").count(), 1)
