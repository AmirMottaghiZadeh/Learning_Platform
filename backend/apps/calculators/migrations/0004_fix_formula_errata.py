from django.db import migrations

from apps.calculators.errata import fix_results


def apply_fixes(apps, schema_editor):
    Calculator = apps.get_model("calculators", "Calculator")
    for calc in Calculator.objects.all().only("pk", "calculator_id", "results"):
        fixed = fix_results(calc.calculator_id, calc.results)
        if fixed != calc.results:
            Calculator.objects.filter(pk=calc.pk).update(results=fixed)


class Migration(migrations.Migration):
    dependencies = [("calculators", "0003_calculator_formula_strings_fa")]

    # Data only: the fix is not undone, the old formulas were wrong.
    operations = [migrations.RunPython(apply_fixes, migrations.RunPython.noop)]
