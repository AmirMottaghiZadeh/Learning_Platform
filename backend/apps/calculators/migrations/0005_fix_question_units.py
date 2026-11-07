from django.db import migrations

from apps.calculators.errata import fix_questions, fix_results


def apply_fixes(apps, schema_editor):
    """Both kinds of correction again (each is a no-op where already done): the
    first migration ran before the later ones were added."""
    Calculator = apps.get_model("calculators", "Calculator")
    for calc in Calculator.objects.all().only("pk", "calculator_id", "results", "questions"):
        results = fix_results(calc.calculator_id, calc.results)
        questions = fix_questions(calc.calculator_id, calc.questions)
        if results != calc.results or questions != calc.questions:
            Calculator.objects.filter(pk=calc.pk).update(results=results, questions=questions)


class Migration(migrations.Migration):
    dependencies = [("calculators", "0004_fix_formula_errata")]

    operations = [migrations.RunPython(apply_fixes, migrations.RunPython.noop)]
