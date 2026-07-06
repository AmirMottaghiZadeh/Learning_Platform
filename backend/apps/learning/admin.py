from django.contrib import admin

from .models import (
    KnowledgeSource,
    LearnerProgress,
    LearningEventRecord,
    LearningObject,
    LearningTopic,
)


@admin.register(LearningTopic)
class LearningTopicAdmin(admin.ModelAdmin):
    list_display = ["product_id", "key", "label", "is_active"]
    search_fields = ["product_id", "key", "label"]
    list_filter = ["product_id", "is_active"]


@admin.register(LearningObject)
class LearningObjectAdmin(admin.ModelAdmin):
    list_display = ["product_id", "external_id", "display_name", "topic", "is_active"]
    search_fields = ["product_id", "external_id", "display_name"]
    list_filter = ["product_id", "is_active"]


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ["product_id", "source_type", "learning_object", "topic", "is_active"]
    search_fields = ["product_id", "source_type", "prompt", "correct_answer"]
    list_filter = ["product_id", "source_type", "is_active"]


@admin.register(LearningEventRecord)
class LearningEventRecordAdmin(admin.ModelAdmin):
    list_display = ["product_id", "event_type", "learner", "occurred_at", "source"]
    search_fields = ["product_id", "event_type", "correlation_id"]
    list_filter = ["product_id", "event_type", "source"]
    readonly_fields = ["event_id", "created_at"]


@admin.register(LearnerProgress)
class LearnerProgressAdmin(admin.ModelAdmin):
    list_display = [
        "product_id",
        "learner",
        "topic",
        "questions_answered",
        "correct_answers",
        "xp",
        "mastery_state",
    ]
    search_fields = ["product_id", "learner__username", "topic__key", "topic__label"]
    list_filter = ["product_id", "mastery_state"]
    readonly_fields = ["created_at", "updated_at"]
