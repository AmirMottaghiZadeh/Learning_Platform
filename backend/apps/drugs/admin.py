from django.contrib import admin

from .models import AtcCode, Ingredient, IngredientProfileSection


@admin.register(AtcCode)
class AtcCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "level"]
    search_fields = ["code", "name"]
    ordering = ["code"]


class IngredientProfileSectionInline(admin.TabularInline):
    model = IngredientProfileSection
    extra = 0
    fields = ["field", "n_contributing_products", "summary_fa", "summary_en", "has_content"]
    readonly_fields = ["field", "n_contributing_products", "has_content"]
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "rxcui", "n_products", "n_source_records", "atc_summary"]
    search_fields = ["name", "rxcui"]
    list_filter = ["atc_codes"]
    ordering = ["name"]
    readonly_fields = ["slug", "created_at", "updated_at", "source_fetched_at"]
    filter_horizontal = ["atc_codes"]
    inlines = [IngredientProfileSectionInline]

    @admin.display(description="ATC")
    def atc_summary(self, obj):
        return ", ".join(obj.atc_codes.values_list("code", flat=True)[:4])


@admin.register(IngredientProfileSection)
class IngredientProfileSectionAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "field", "n_contributing_products", "has_summary"]
    list_filter = ["field"]
    search_fields = ["ingredient__name", "ingredient__rxcui"]
    list_select_related = ["ingredient"]
    readonly_fields = ["ingredient", "field", "raw_text", "n_contributing_products", "updated_at"]
