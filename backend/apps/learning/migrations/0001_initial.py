# Generated manually for the platform learning domain core.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LearningTopic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.CharField(default="platform", max_length=80)),
                ("key", models.CharField(max_length=80)),
                ("label", models.CharField(max_length=160)),
                ("detail", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["product_id", "key"], name="learning_le_product_ca27b1_idx"),
                    models.Index(fields=["is_active"], name="learning_le_is_acti_63ca48_idx"),
                ],
                "unique_together": {("product_id", "key")},
            },
        ),
        migrations.CreateModel(
            name="LearningObject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.CharField(default="platform", max_length=80)),
                ("external_id", models.CharField(max_length=120)),
                ("display_name", models.CharField(max_length=255)),
                ("subtitle", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "topic",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="learning_objects",
                        to="learning.learningtopic",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["product_id", "external_id"], name="learning_le_product_5f7c30_idx"),
                    models.Index(fields=["product_id", "is_active"], name="learning_le_product_b79b72_idx"),
                ],
                "unique_together": {("product_id", "external_id")},
            },
        ),
        migrations.CreateModel(
            name="LearningEventRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("event_type", models.CharField(max_length=120)),
                ("product_id", models.CharField(max_length=80)),
                ("occurred_at", models.DateTimeField()),
                ("correlation_id", models.CharField(blank=True, max_length=120)),
                ("source", models.CharField(default="backend", max_length=120)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "learner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="learning_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["product_id", "event_type", "occurred_at"], name="learning_le_product_b62fca_idx"),
                    models.Index(fields=["learner", "occurred_at"], name="learning_le_learner_99292b_idx"),
                    models.Index(fields=["correlation_id"], name="learning_le_correla_5a4ab6_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="KnowledgeSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.CharField(default="platform", max_length=80)),
                ("external_id", models.CharField(max_length=160)),
                ("source_type", models.CharField(max_length=80)),
                ("prompt", models.TextField()),
                ("correct_answer", models.TextField()),
                ("explanation", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "learning_object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="knowledge_sources",
                        to="learning.learningobject",
                    ),
                ),
                (
                    "topic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="knowledge_sources",
                        to="learning.learningtopic",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["product_id", "external_id"], name="learning_kn_product_9b1bd6_idx"),
                    models.Index(fields=["product_id", "source_type", "is_active"], name="learning_kn_product_02d71c_idx"),
                    models.Index(fields=["product_id", "topic", "is_active"], name="learning_kn_product_1a081c_idx"),
                ],
                "unique_together": {("product_id", "external_id")},
            },
        ),
    ]
