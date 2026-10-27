from django.db import migrations, models

from apps.drugs.data.atc_l4_fa import ATC_L4_FA


def fill_name_fa(apps, schema_editor):
    AtcCode = apps.get_model("drugs", "AtcCode")
    for code in AtcCode.objects.filter(code__in=ATC_L4_FA.keys(), name_fa=""):
        code.name_fa = ATC_L4_FA[code.code]
        code.save(update_fields=["name_fa"])


class Migration(migrations.Migration):

    dependencies = [
        ("drugs", "0004_remove_misfit_atc_codes"),
    ]

    operations = [
        migrations.AddField(
            model_name="atccode",
            name="name_fa",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(fill_name_fa, migrations.RunPython.noop),
    ]
