from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flashcards", "0004_separate_new_cards_from_leitner"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="flashcardstate",
            index=models.Index(
                fields=["user", "box", "review_state"],
                name="flashcards__user_id_c46a2e_idx",
            ),
        ),
    ]
