"""The UpToDate feature is named just "UpToDate" on the plans page, not
"مقالات UpToDate فارسی". A name an operator has already changed in the
console is left as it is."""

from django.db import migrations

OLD = "مقالات UpToDate فارسی"
NEW = "UpToDate"


def rename(apps, schema_editor):
    Feature = apps.get_model("billing", "Feature")
    Feature.objects.filter(key="uptodate", name_fa=OLD).update(name_fa=NEW)


def restore(apps, schema_editor):
    Feature = apps.get_model("billing", "Feature")
    Feature.objects.filter(key="uptodate", name_fa=NEW).update(name_fa=OLD)


class Migration(migrations.Migration):
    dependencies = [("billing", "0009_billingsettings_signup_gift_days_and_more")]
    operations = [migrations.RunPython(rename, restore)]
