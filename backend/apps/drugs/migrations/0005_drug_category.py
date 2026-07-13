from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drugs", "0004_alter_drug_consumption_time_sorted"),
    ]

    operations = [
        migrations.AddField(
            model_name="drug",
            name="category",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
