from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_retrieval", "0005_reference_media_catalog")]
    operations = [migrations.CreateModel(
        name="SourceLinkMap",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("source_generation", models.UUIDField()),
            ("source_id", models.CharField(max_length=32)),
            ("content_hash", models.CharField(max_length=64)),
            ("parser_version", models.CharField(max_length=128)),
            ("links", models.JSONField(default=dict)),
        ],
        options={"constraints":[models.UniqueConstraint(fields=("source_generation","source_id","content_hash","parser_version"),
            name="source_link_map_once")]},
    )]
