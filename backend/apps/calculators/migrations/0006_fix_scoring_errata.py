from django.db import migrations

from apps.calculators.errata import fix_questions, fix_results, fix_strings_fa


def apply_fixes(apps, schema_editor):
    """The corrections again (each is a no-op where already done), now with
    the scoring fixes of fourteen calculators: formulas, choice weights, a
    missing choice, and the Persian for the text the fixed formulas return."""
    Calculator = apps.get_model("calculators", "Calculator")
    for calc in Calculator.objects.all().only("pk", "calculator_id", "results", "questions", "formula_strings_fa"):
        results = fix_results(calc.calculator_id, calc.results)
        questions = fix_questions(calc.calculator_id, calc.questions)
        strings = fix_strings_fa(calc.calculator_id, calc.formula_strings_fa)
        if results != calc.results or questions != calc.questions or strings != calc.formula_strings_fa:
            Calculator.objects.filter(pk=calc.pk).update(results=results, questions=questions, formula_strings_fa=strings)


class Migration(migrations.Migration):
    dependencies = [("calculators", "0005_fix_question_units")]

    operations = [migrations.RunPython(apply_fixes, migrations.RunPython.noop)]
