from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("website", "0008_sitesettings_hero_motion_enabled")]

    operations = [
        migrations.RemoveField(model_name="sitesettings", name="hero_motion_enabled"),
    ]
