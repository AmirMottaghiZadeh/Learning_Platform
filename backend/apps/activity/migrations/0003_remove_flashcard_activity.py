from django.db import migrations


def remove_retired_events(apps, schema_editor):
    apps.get_model("activity", "ActivityEvent").objects.using(schema_editor.connection.alias).filter(section__in=["flashcards", "leitner"]).delete()


class Migration(migrations.Migration):
    dependencies = [("activity", "0002_activityevent_area_activityevent_viewport_and_more")]
    operations = [migrations.RunPython(remove_retired_events, migrations.RunPython.noop)]
