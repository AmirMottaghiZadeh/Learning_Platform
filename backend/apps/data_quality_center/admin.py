from django.contrib import admin

from .models import SectionEdit, SectionEditRequest


@admin.register(SectionEdit)
class SectionEditAdmin(admin.ModelAdmin):
    list_display = ["created_at", "ingredient_name", "field", "editor_username", "approved_by_username"]
    list_filter = ["field", "created_at"]
    search_fields = ["ingredient_name", "editor_username", "approved_by_username", "reason"]
    readonly_fields = [f.name for f in SectionEdit._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SectionEditRequest)
class SectionEditRequestAdmin(admin.ModelAdmin):
    list_display = ["created_at", "ingredient_name", "field", "status", "requested_by_username", "reviewed_by_username"]
    list_filter = ["status", "field", "created_at"]
    search_fields = ["ingredient_name", "requested_by_username", "reviewed_by_username", "reason"]
    readonly_fields = [
        f.name for f in SectionEditRequest._meta.fields
        if f.name not in {"status", "review_note"}
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
