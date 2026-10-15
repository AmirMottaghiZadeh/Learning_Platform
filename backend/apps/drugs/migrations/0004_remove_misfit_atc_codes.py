"""Drop ATC codes an ingredient carries but is no longer indicated for.

ATC keeps legacy classes: apomorphine still has G04BE (erectile dysfunction)
from its old sublingual use, although its only labelled indication today is
Parkinson's disease -- so the lessons filed it under Urology. For each
ingredient below, every ATC code under the listed L2 chapter(s) is removed;
its other codes stay. Chosen by comparing each multi-chapter ingredient's
"Indications and usage" with the scope of each chapter it sat in, keeping
only clearly unrelated pairs.

The same cleanup was applied to the upstream pipeline database
(ingredient_clinical_profiles.atc_codes and ingredient_atc_codes, backup in
table atc_backup_2026_10_16), so a re-run of import_openfda does not bring the codes back. This migration carries it to databases that
were loaded earlier (production). Idempotent; not reversible.
"""

from django.db import migrations

# RxNorm ingredient RXCUI -> ATC L2 chapters to drop for it
REMOVE = {
    "44": ["R05"],
    "110": ["A01", "D08", "R02"],
    "168": ["G01"],
    "281": ["S01"],
    "569": ["P01"],
    "641": ["D06", "S01"],
    "732": ["A01", "A07", "G01"],
    "733": ["S01"],
    "1043": ["G04"],
    "1291": ["R02"],
    "1347": ["A07", "D07"],
    "1378": ["R02"],
    "1514": ["C05"],
    "1886": ["D11"],
    "1894": ["D05"],
    "1999": ["N07"],
    "2116": ["C07"],
    "2194": ["S01"],
    "2286": ["B05", "D08", "D09"],
    "2348": ["D10"],
    "2358": ["B05", "S01", "S02", "S03"],
    "2590": ["S01"],
    "2599": ["S01"],
    "2623": ["A01"],
    "2653": ["R02", "S01", "S02"],
    "3143": ["A14"],
    "3254": ["S01"],
    "3264": ["A01", "C05"],
    "3327": ["C02"],
    "3339": ["S01", "S02"],
    "3443": ["C05"],
    "3554": ["P03"],
    "3743": ["G01"],
    "3966": ["R01", "S01"],
    "3992": ["A01", "B02", "R01"],
    "4124": ["L02"],
    "4328": ["A08"],
    "4451": ["D01"],
    "4462": ["C05"],
    "4491": ["C05", "D07", "D10"],
    "4502": ["R02"],
    "4550": ["S02"],
    "5224": ["S01"],
    "5781": ["S01"],
    "5942": ["G01", "P01", "S02"],
    "6135": ["G01"],
    "6628": ["A06", "R05"],
    "6847": ["N05"],
    "6902": ["D10"],
    "6922": ["A01"],
    "6932": ["A07", "S02"],
    "7242": ["A06"],
    "7268": ["A01", "A07", "D01", "G01"],
    "7299": ["A01", "B05", "R02", "S01", "S02", "S03"],
    "7315": ["S01"],
    "7597": ["G01"],
    "7676": ["N02"],
    "7812": ["S01"],
    "7980": ["S01"],
    "8299": ["S01"],
    "8356": ["S01"],
    "8410": ["S01"],
    "8536": ["A07", "S02"],
    "8638": ["A01", "C05"],
    "9525": ["S01"],
    "9601": ["N05", "S01"],
    "10109": ["A07"],
    "10391": ["C05"],
    "10395": ["A01", "S02"],
    "10759": ["A01", "C05"],
    "11002": ["B05"],
    "11124": ["S01"],
    "18889": ["D04"],
    "19143": ["D02"],
    "19831": ["D07"],
    "21090": ["G01"],
    "22701": ["S01"],
    "23043": ["D07"],
    "25120": ["R03"],
    "26849": ["R01", "R02", "S01", "S03"],
    "32638": ["G01"],
    "33290": ["C05"],
    "35302": ["S01"],
    "35382": ["S01"],
    "35619": ["D06"],
    "36435": ["G01"],
    "37935": ["R01"],
    "38298": ["D01"],
    "39841": ["S01"],
    "42331": ["G02"],
    "47579": ["N04"],
    "68099": ["S01"],
    "89785": ["S01"],
    "108088": ["S01"],
    "115238": ["A01"],
    "253337": ["S01"],
}


def remove_codes(apps, schema_editor):
    Ingredient = apps.get_model("drugs", "Ingredient")
    for rxcui, chapters in REMOVE.items():
        ingredient = Ingredient.objects.filter(rxcui=rxcui).first()
        if ingredient is None:
            continue
        stale = [c for c in ingredient.atc_codes.all() if c.code[:3] in chapters]
        # Never strip an ingredient of every code: that would drop it from the
        # lessons altogether.
        if stale and len(stale) < ingredient.atc_codes.count():
            ingredient.atc_codes.remove(*stale)


class Migration(migrations.Migration):

    dependencies = [
        ("drugs", "0003_ingredient_name_fa"),
    ]

    operations = [
        migrations.RunPython(remove_codes, migrations.RunPython.noop),
    ]
