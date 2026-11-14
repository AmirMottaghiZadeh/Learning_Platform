import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone


class CreditSettings(models.Model):
    enabled = models.BooleanField(default=False)
    initial_credits = models.DecimalField(max_digits=22, decimal_places=6, default=100)
    input_per_million = models.DecimalField(max_digits=22, decimal_places=6, default=1000)
    cached_input_per_million = models.DecimalField(max_digits=22, decimal_places=6, null=True, blank=True, default=100)
    cache_write_per_million = models.DecimalField(max_digits=22, decimal_places=6, null=True, blank=True, default=1250)
    cache_write_12h_per_million = models.DecimalField(max_digits=22, decimal_places=6, null=True, blank=True, default=2500)
    output_per_million = models.DecimalField(max_digits=22, decimal_places=6, default=1000)
    embedding_per_million = models.DecimalField(max_digits=22, decimal_places=6, default=200)
    usd_per_1000_credits = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.60"))
    usd_to_toman = models.PositiveBigIntegerField(default=270000)
    fx_mode = models.CharField(max_length=10, choices=[("manual", "نرخ دستی"), ("tgju", "آخرین نرخ دلار آزاد TGJU")], default="tgju")
    fx_source = models.CharField(max_length=20, default="manual")
    fx_quoted_at = models.DateTimeField(default=timezone.now)
    fx_checked_at = models.DateTimeField(null=True, blank=True)
    model_signature = models.CharField(max_length=64, blank=True)
    revision = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(initial_credits__gte=0, input_per_million__gte=0,
            output_per_million__gte=0, embedding_per_million__gte=0)
            & (Q(cached_input_per_million__isnull=True) | Q(cached_input_per_million__gte=0))
            & (Q(cache_write_per_million__isnull=True) | Q(cache_write_per_million__gte=0))
            & (Q(cache_write_12h_per_million__isnull=True) | Q(cache_write_12h_per_million__gte=0)), name="ai_credit_rates_nonnegative"),
            models.CheckConstraint(condition=Q(usd_to_toman__gt=0, usd_per_1000_credits__gt=0), name="ai_credit_fx_positive")]


class CreditPackage(models.Model):
    name = models.CharField(max_length=100)
    credits = models.DecimalField(max_digits=22, decimal_places=6)
    price_toman = models.PositiveBigIntegerField()
    dollar_priced = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.CheckConstraint(condition=Q(credits__gt=0, price_toman__gt=0), name="ai_credit_package_positive")]

    def __str__(self):
        return self.name


class CreditWallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="search_wallet")
    balance = models.DecimalField(max_digits=22, decimal_places=6, default=0)
    initial_awarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available(self):
        return self.balance


class CreditReservation(models.Model):
    # Legacy model name, now a usage record only. No credits are reserved.
    # The UUID remains independent from result retention and existing ledger.
    id = models.UUIDField(primary_key=True, editable=False)
    wallet = models.ForeignKey(CreditWallet, on_delete=models.PROTECT, related_name="reservations")
    status = models.CharField(max_length=16, default="tracking", choices=[("tracking", "در حال محاسبه"), ("pending", "در انتظار بررسی مصرف"), ("settled", "تسویه‌شده")])
    charged = models.DecimalField(max_digits=22, decimal_places=6, default=0)
    pricing = models.JSONField(default=dict)
    prompt_tokens = models.PositiveBigIntegerField(default=0)
    completion_tokens = models.PositiveBigIntegerField(default=0)
    embedding_tokens = models.PositiveBigIntegerField(default=0)
    cached_tokens = models.PositiveBigIntegerField(default=0)
    cache_write_tokens = models.PositiveBigIntegerField(default=0)
    unknown_attempts = models.PositiveIntegerField(default=0)
    outcome = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["wallet", "status"], name="ai_credit_reservation_state")]
        constraints = [models.CheckConstraint(condition=Q(charged__gte=0), name="ai_credit_charge_nonnegative")]


class CreditAttempt(models.Model):
    reservation = models.ForeignKey(CreditReservation, on_delete=models.CASCADE, related_name="attempts")
    sequence = models.PositiveIntegerField()
    kind = models.CharField(max_length=10, choices=[("chat", "پاسخ‌گو"), ("embedding", "بردارسازی پرسش")])
    usage = models.JSONField(default=dict)
    known = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["reservation", "sequence"], name="ai_credit_attempt_once")]


class CreditEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(CreditWallet, on_delete=models.PROTECT, related_name="entries")
    source_key = models.CharField(max_length=160, unique=True)
    kind = models.CharField(max_length=16, choices=[("initial", "اعتبار اولیه"), ("topup", "شارژ اعتبار"), ("search", "جست‌وجوی هوشمند"), ("adjustment", "اصلاح اعتبار")])
    amount = models.DecimalField(max_digits=22, decimal_places=6)
    balance_after = models.DecimalField(max_digits=22, decimal_places=6)
    note = models.CharField(max_length=255, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="search_credit_actions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["wallet", "-created_at"], name="ai_credit_entry_history")]
