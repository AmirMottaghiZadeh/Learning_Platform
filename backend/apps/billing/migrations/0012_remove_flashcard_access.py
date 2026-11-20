"""Retire the removed feature and its per-user usage without altering orders."""
from django.db import migrations


def retire_feature(apps, schema_editor):
    db = schema_editor.connection.alias
    apps.get_model("billing", "UsageRecord").objects.using(db).filter(feature_key="flashcards").delete()
    apps.get_model("billing", "Feature").objects.using(db).filter(key="flashcards").delete()
    Entitlement = apps.get_model("billing", "Entitlement")
    for entitlement in Entitlement.objects.using(db).all().iterator():
        if "flashcards" in entitlement.features:
            entitlement.features.pop("flashcards")
            entitlement.save(using=db, update_fields=["features"])


class Migration(migrations.Migration):
    dependencies = [("billing", "0011_order_channel")]
    operations = [migrations.RunPython(retire_feature, migrations.RunPython.noop)]
