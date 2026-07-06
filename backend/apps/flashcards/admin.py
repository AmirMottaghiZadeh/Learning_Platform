from django.contrib import admin

from .models import FlashcardReview, FlashcardState


@admin.register(FlashcardState)
class FlashcardStateAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "knowledge_source",
        "box",
        "review_state",
        "review_count",
        "lapse_count",
        "due_at",
        "last_reviewed_at",
    ]
    list_filter = ["box", "review_state", "schedule_rule_version"]
    search_fields = [
        "user__username",
        "knowledge_source__prompt",
        "knowledge_source__correct_answer",
        "knowledge_source__source_type",
    ]
    readonly_fields = ["last_reviewed_at"]


@admin.register(FlashcardReview)
class FlashcardReviewAdmin(admin.ModelAdmin):
    list_display = [
        "state",
        "rating",
        "box_before",
        "box_after",
        "interval_days",
        "created_at",
    ]
    list_filter = ["rating", "box_before", "box_after", "rule_version"]
    search_fields = ["state__user__username", "state__knowledge_source__prompt"]
    readonly_fields = ["created_at"]
