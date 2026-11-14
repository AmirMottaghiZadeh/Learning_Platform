from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Ingredient, IngredientProfileSection


@receiver(post_delete, sender=IngredientProfileSection)
def invalidate_deleted_section_review(sender, instance, using, **kwargs):
    # A removed section cannot be detected by the remaining sections' dates.
    Ingredient.objects.using(using).filter(pk=instance.ingredient_id).update(
        reviewed_at=None, reviewed_by_username=""
    )
