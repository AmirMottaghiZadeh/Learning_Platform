from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0008_bankquestion_explanation_en_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quizquestion",
            name="prompt_fa",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="quizquestion",
            name="prompt_en",
            field=models.TextField(),
        ),
    ]
