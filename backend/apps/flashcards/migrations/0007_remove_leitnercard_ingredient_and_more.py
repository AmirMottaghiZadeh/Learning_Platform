"""Permanently remove all users' flashcard history; keep shared quiz facts."""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("flashcards", "0006_leitner_by_section"),
        ("quiz", "0010_studyfact"),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[migrations.DeleteModel(name="FlashcardFact")]),
        migrations.DeleteModel(name="LeitnerCard"),
        migrations.DeleteModel(name="TopicProgress"),
    ]
