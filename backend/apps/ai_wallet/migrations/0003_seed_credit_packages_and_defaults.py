"""Product defaults approved by the owner; never fetch external data in a migration."""
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
import json

from django.conf import settings
from django.db import migrations


def seed(apps, schema_editor):
    Config = apps.get_model("ai_wallet", "CreditSettings")
    Package = apps.get_model("ai_wallet", "CreditPackage")
    alias = schema_editor.connection.alias
    config, created = Config.objects.using(alias).get_or_create(pk=1)
    unconfigured = created or not any((config.input_per_million, config.output_per_million, config.embedding_per_million))
    if config.initial_credits == 0:
        config.initial_credits = Decimal(100)
    if unconfigured:
        config.input_per_million = config.output_per_million = Decimal(1000)
        config.cached_input_per_million = Decimal(100)
        config.cache_write_per_million = Decimal(1250)
        config.cache_write_12h_per_million = Decimal(2500)
        config.embedding_per_million = Decimal(200)
        config.search_reserve = Decimal(100)
        # Only match the preset to the models it was reviewed for. Other
        # providers/models remain subject to explicit tariff review.
        if settings.AI_LAB_MODEL == "gpt-6-luna" and settings.AI_LAB_EMBEDDING_MODEL == "text-embedding-3-small":
            values = [settings.AI_LAB_MODEL, settings.AI_LAB_BASE_URL.rstrip("/"), settings.AI_LAB_SEARCH_ENGINE,
                      settings.AI_LAB_EMBEDDING_MODEL, settings.AI_LAB_EMBEDDING_BASE_URL.rstrip("/"),
                      settings.AI_LAB_EMBEDDING_DIMENSIONS, settings.AI_LAB_EMBEDDING_REVISION]
            config.model_signature = sha256(json.dumps(values).encode()).hexdigest()
            config.enabled = settings.AI_LAB_SEARCH_ENGINE == "hybrid"
    config.save(using=alias)
    for order, count in enumerate((500, 1000, 2000)):
        if Package.objects.using(alias).filter(credits=count).exists():
            continue  # Preserve packages already configured by the manager.
        price = int((Decimal(count)/1000 * config.usd_per_1000_credits
                     * config.usd_to_toman).to_integral_value(rounding=ROUND_CEILING))
        Package.objects.using(alias).create(name=f"بستهٔ {count} اعتباری", credits=count,
            dollar_priced=True, price_toman=price, active=True, order=order)


class Migration(migrations.Migration):
    dependencies = [("ai_wallet", "0002_credit_defaults_fx_and_cache_writes")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
