"""One review status for the current published drug, shared by all readers."""

from django.db.models import BooleanField, Case, Exists, F, OuterRef, Value, When

from .models import IngredientProfileSection


def with_review_status(queryset):
    newer_sections = IngredientProfileSection.objects.filter(
        ingredient_id=OuterRef("pk"), updated_at__gt=OuterRef("reviewed_at")
    )
    return queryset.annotate(_newer_sections=Exists(newer_sections)).annotate(
        _is_reviewed=Case(
            When(reviewed_at__isnull=False, reviewed_at__gte=F("updated_at"),
                 _newer_sections=False, then=Value(True)),
            default=Value(False), output_field=BooleanField(),
        )
    )
