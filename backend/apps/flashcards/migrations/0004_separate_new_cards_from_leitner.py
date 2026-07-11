from django.db import migrations


def clear_new_card_due_dates(apps, schema_editor):
    FlashcardState = apps.get_model("flashcards", "FlashcardState")
    FlashcardState.objects.filter(box=0, review_state="new").update(due_at=None)


class Migration(migrations.Migration):
    dependencies = [
        ("flashcards", "0003_phase5_progress_review"),
    ]

    operations = [
        migrations.RunPython(clear_new_card_due_dates, migrations.RunPython.noop),
    ]
