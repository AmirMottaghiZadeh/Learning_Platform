from django.contrib import admin

from .models import FlashcardFact, LeitnerCard


@admin.register(LeitnerCard)
class LeitnerCardAdmin(admin.ModelAdmin):
    list_display = ["user", "ingredient", "box", "due_at", "times_seen"]
    list_filter = ["box"]
    search_fields = ["user__username", "ingredient__name"]
    autocomplete_fields = ["ingredient"]


@admin.register(FlashcardFact)
class FlashcardFactAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "section", "lang", "order", "text"]
    list_filter = ["section", "lang"]
    search_fields = ["ingredient__name", "text"]
    autocomplete_fields = ["ingredient"]
