from django.contrib import admin

from .models import ReviewEvent, SectionEdit, SectionEditRequest


class ReadOnlyAdmin(admin.ModelAdmin):
    """Everything here is changed only through the console's workflow, which
    writes the audit trail; the admin just shows it. Editing a request's
    status here would skip both the approval and the audit."""

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SectionEdit)
class SectionEditAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "ingredient_name", "field", "editor_username", "approved_by_username"]
    list_filter = ["field", "created_at"]
    search_fields = ["ingredient_name", "editor_username", "approved_by_username", "reason"]


@admin.register(SectionEditRequest)
class SectionEditRequestAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "ingredient_name", "field", "status", "requested_by_username", "reviewed_by_username"]
    list_filter = ["status", "field", "created_at"]
    search_fields = ["ingredient_name", "requested_by_username", "reviewed_by_username", "reason"]


@admin.register(ReviewEvent)
class ReviewEventAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "action", "actor_username", "request", "ip_address"]
    list_filter = ["action", "created_at"]
    search_fields = ["actor_username", "request__ingredient_name", "note"]
