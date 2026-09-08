from django.contrib import admin

from .models import LeitnerCard


@admin.register(LeitnerCard)
class LeitnerCardAdmin(admin.ModelAdmin):
    list_display = ["user", "ingredient", "box", "due_at", "times_seen"]
    list_filter = ["box"]
    search_fields = ["user__username", "ingredient__name"]
    autocomplete_fields = ["ingredient"]
