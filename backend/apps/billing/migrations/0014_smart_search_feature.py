"""Make smart search selectable in plans without removing existing public access."""
from django.db import migrations


def seed(apps, schema_editor):
    db = schema_editor.connection.alias
    Feature = apps.get_model("billing", "Feature")
    Plan = apps.get_model("billing", "Plan")
    PlanFeature = apps.get_model("billing", "PlanFeature")
    feature, created = Feature.objects.using(db).get_or_create(
        key="smart_search",
        defaults={
            "name_fa": "سرچ هوشمند",
            "name_en": "Smart search",
            "description_fa": "دسترسی به سرچ هوشمند؛ مصرف هر جست‌وجو از اعتبار جداگانهٔ کاربر کسر می‌شود.",
            "kind": "builtin",
            "countable": False,
            "unit_fa": "",
            "order": 10,
        },
    )
    if not created:
        # Preserve an operator's names, activation and plan assignments if a
        # custom feature with this key was already configured.
        Feature.objects.using(db).filter(pk=feature.pk).update(kind="builtin", countable=False, unit_fa="")
        return
    free = Plan.objects.using(db).filter(is_free=True).first()
    if free is not None:
        PlanFeature.objects.using(db).get_or_create(plan_id=free.pk, feature_id=feature.pk)


class Migration(migrations.Migration):
    dependencies = [("billing", "0013_order_credit_amount_order_credit_package_and_more")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
