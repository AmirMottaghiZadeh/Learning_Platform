from django.db import migrations

from apps.core.units_fa import standardize_units


def apply(apps, schema_editor):
    """The units in the Persian lesson summaries as standard symbols
    («میلی‌گرم بر کیلوگرم در روز» -> «mg/kg/day»; see apps.core.units_fa)."""
    Section = apps.get_model("drugs", "IngredientProfileSection")
    changed = []
    for section in Section.objects.exclude(summary_fa="").only("pk", "summary_fa").iterator(chunk_size=500):
        fixed = standardize_units(section.summary_fa)
        if fixed != section.summary_fa:
            section.summary_fa = fixed
            changed.append(section)
        if len(changed) >= 500:
            Section.objects.bulk_update(changed, ["summary_fa"])
            changed = []
    if changed:
        Section.objects.bulk_update(changed, ["summary_fa"])


class Migration(migrations.Migration):
    dependencies = [("drugs", "0005_atccode_name_fa")]

    # Data only, not undone: the Persian unit spellings are not wanted back.
    operations = [migrations.RunPython(apply, migrations.RunPython.noop)]
