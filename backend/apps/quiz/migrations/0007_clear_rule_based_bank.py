from django.db import migrations


def clear_bank(apps, schema_editor):
    """The rule-based question bank is retired: its questions were pieced
    together from other drugs' facts, with no check that a wrong option really
    is wrong for the drug asked about. Questions already in a learner's past
    sessions are kept (QuizQuestion holds its own copy); the new bank, made by
    the study-content pipeline, is loaded separately."""
    apps.get_model("quiz", "BankQuestion").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("quiz", "0006_bank_fields_card_sections")]

    operations = [migrations.RunPython(clear_bank, migrations.RunPython.noop)]
