from django.db import migrations


def clear_facts(apps, schema_editor):
    """The rule-based card facts are retired along with the question bank. A
    learner's own cards (box, due date) are kept; what a card says arrives
    with the content built by the study-content pipeline."""
    apps.get_model("flashcards", "FlashcardFact").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("flashcards", "0003_topicprogress")]

    operations = [migrations.RunPython(clear_facts, migrations.RunPython.noop)]
