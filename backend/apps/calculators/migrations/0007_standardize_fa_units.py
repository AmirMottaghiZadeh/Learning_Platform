from django.db import migrations

from apps.calculators.errata import standardize_fa_units

FIELDS = ("name_fa", "description_fa", "about_fa", "disclaimer_footer_fa", "questions", "results", "error_checks", "formula_strings_fa")


def apply(apps, schema_editor):
    """The units in every calculator's Persian text as standard symbols
    («میلی‌گرم بر کیلوگرم» -> «mg/kg»; see apps.core.units_fa)."""
    Calculator = apps.get_model("calculators", "Calculator")
    for calc in Calculator.objects.all().only("pk", *FIELDS):
        current = {name: getattr(calc, name) for name in FIELDS}
        fixed = standardize_fa_units(current)
        changed = {name: value for name, value in fixed.items() if value != current[name]}
        if changed:
            Calculator.objects.filter(pk=calc.pk).update(**changed)


class Migration(migrations.Migration):
    dependencies = [("calculators", "0006_fix_scoring_errata")]

    # Data only, not undone: the Persian unit spellings are not wanted back.
    operations = [migrations.RunPython(apply, migrations.RunPython.noop)]
