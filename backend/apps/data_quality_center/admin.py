from django.contrib import admin

from .models import SectionEdit


@admin.register(SectionEdit)
class SectionEditAdmin(admin.ModelAdmin):
    list_display = ["created_at", "ingredient_name", "field", "editor_username"]
    list_filter = ["field", "created_at"]
    search_fields = ["ingredient_name", "editor_username", "reason"]
    readonly_fields = [f.name for f in SectionEdit._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
