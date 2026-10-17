"""Gateways become rows of their own, so the console can hold more than one.
A Zarinpal merchant id saved in the console carries over as an enabled
Zarinpal row, with its sandbox switch and last connection test."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_zarinpal_settings(apps, schema_editor):
    BillingSettings = apps.get_model("billing", "BillingSettings")
    PaymentGateway = apps.get_model("billing", "PaymentGateway")
    row = BillingSettings.objects.first()
    if row is None or not row.zarinpal_merchant_id:
        return
    sandbox = settings.ZARINPAL_SANDBOX if row.zarinpal_sandbox is None else row.zarinpal_sandbox
    PaymentGateway.objects.create(
        kind="zarinpal", is_enabled=True, priority=10, merchant_id=row.zarinpal_merchant_id, sandbox=sandbox,
        last_test_at=row.last_test_at, last_test_ok=row.last_test_ok, last_test_message=row.last_test_message,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_keep_orders_of_deleted_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='gateway_ref',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.CreateModel(
            name='PaymentGateway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('zarinpal', 'زرین\u200cپال'), ('sep', 'سامان (سپ)')], max_length=20, unique=True)),
                ('title', models.CharField(blank=True, max_length=60)),
                ('is_enabled', models.BooleanField(default=True)),
                ('priority', models.PositiveSmallIntegerField(default=10)),
                ('merchant_id', models.CharField(blank=True, max_length=64)),
                ('sandbox', models.BooleanField(default=False)),
                ('last_test_at', models.DateTimeField(blank=True, null=True)),
                ('last_test_ok', models.BooleanField(blank=True, null=True)),
                ('last_test_message', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['priority', 'id'],
            },
        ),
        migrations.RunPython(copy_zarinpal_settings, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='billingsettings',
            name='gateway',
        ),
        migrations.RemoveField(
            model_name='billingsettings',
            name='last_test_at',
        ),
        migrations.RemoveField(
            model_name='billingsettings',
            name='last_test_message',
        ),
        migrations.RemoveField(
            model_name='billingsettings',
            name='last_test_ok',
        ),
        migrations.RemoveField(
            model_name='billingsettings',
            name='zarinpal_merchant_id',
        ),
        migrations.RemoveField(
            model_name='billingsettings',
            name='zarinpal_sandbox',
        ),
    ]
