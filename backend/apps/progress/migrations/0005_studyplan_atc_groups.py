from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progress", "0004_remove_learnerprogress_total_reviews_and_more")]

    operations = [
        migrations.AddField(model_name="studyplan", name="atc_groups", field=models.JSONField(blank=True, default=list)),
    ]
