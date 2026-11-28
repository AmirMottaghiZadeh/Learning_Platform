"""The built-in features, and a free plan holding all of them uncapped -- so
switching BILLING_ENFORCEMENT_ENABLED on changes nothing for anyone until an
operator narrows the free plan in the console."""

from django.db import migrations

BUILTIN = [
    ("lessons", "درس‌نامه‌های دارویی", "Drug lessons", False, ""),
    ("uptodate", "مقالات UpToDate فارسی", "UpToDate articles", True, "مقاله"),
    ("lexicomp", "اطلاعات و تداخل‌های Lexicomp", "Lexicomp interactions", True, "بررسی تداخل"),
    ("medscape", "بیماری‌ها و گایدلاین‌های Medscape", "Medscape diseases and guidelines", True, "مقاله"),
    ("calculators", "ماشین‌حساب‌های بالینی", "Clinical calculators", True, "ماشین‌حساب"),
    ("flashcards", "فلش‌کارت", "Flashcards", True, "کارت"),
    ("quiz", "آزمون‌ها", "Quizzes", True, "سؤال"),
    ("stats", "آمار و برنامه‌ریزی مطالعه", "Statistics and study planning", False, ""),
]


def seed(apps, schema_editor):
    Feature = apps.get_model("billing", "Feature")
    Plan = apps.get_model("billing", "Plan")
    PlanFeature = apps.get_model("billing", "PlanFeature")
    features = []
    for order, (key, fa, en, countable, unit) in enumerate(BUILTIN, start=1):
        feature, _ = Feature.objects.update_or_create(
            key=key,
            defaults={"name_fa": fa, "name_en": en, "kind": "builtin", "countable": countable, "unit_fa": unit, "order": order},
        )
        features.append(feature)
    if not Plan.objects.filter(is_free=True).exists():
        free = Plan.objects.create(
            kind="plan", slug="free", name_fa="رایگان", name_en="Free",
            tagline_fa="آنچه هر کاربر بدون خرید دارد", is_free=True, order=0,
        )
        PlanFeature.objects.bulk_create(PlanFeature(plan=free, feature=f) for f in features)


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
