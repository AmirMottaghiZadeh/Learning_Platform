from decimal import Decimal, ROUND_CEILING
from django.db import migrations


def update_defaults(apps, schema_editor):
    alias = schema_editor.connection.alias
    Package = apps.get_model("ai_wallet", "CreditPackage")
    Config = apps.get_model("ai_wallet", "CreditSettings")
    config = Config.objects.using(alias).filter(pk=1).first()
    rate = config.usd_to_toman if config else 270000
    usd = config.usd_per_1000_credits if config else Decimal("0.60")
    if not Package.objects.using(alias).filter(credits=100).exists():
        price = int((Decimal("0.1") * usd * rate).to_integral_value(rounding=ROUND_CEILING))
        Package.objects.using(alias).create(name="بستهٔ 100 اعتباری",credits=100,
            dollar_priced=True,price_toman=price,active=True,order=0)
    for order, count in enumerate((100, 500, 1000)):
        Package.objects.using(alias).filter(name=f"بستهٔ {count} اعتباری",credits=count,dollar_priced=True).update(order=order)
    # Keep invoice/ledger references to the old default; archive only our seed.
    Package.objects.using(alias).filter(name="بستهٔ 2000 اعتباری",credits=2000,dollar_priced=True).update(active=False)


class Migration(migrations.Migration):
    dependencies = [("ai_wallet", "0003_seed_credit_packages_and_defaults")]
    operations = [migrations.RunPython(update_defaults,migrations.RunPython.noop)]
