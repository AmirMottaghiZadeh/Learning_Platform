from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0006_payment_gateways"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paymentgateway",
            name="kind",
            field=models.CharField(
                choices=[
                    ("zarinpal", "زرین\u200cپال"),
                    ("sep", "سامان (سپ)"),
                    ("zibal", "زیبال"),
                ],
                max_length=20,
                unique=True,
            ),
        ),
    ]
