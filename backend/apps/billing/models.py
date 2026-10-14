"""Plans, one-off products and who may use what.

A Plan (kind "plan": a subscription tier, or "product": something sold on
its own) is a set of Features, each optionally capped per day or month, and
a few prices -- one per duration. Buying one gives the learner an
Entitlement that carries a snapshot of the plan's features at that moment,
so a later edit of the plan only reaches later buyers. The one plan marked
`is_free` is what every learner has without paying, read live.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .catalog import BUILTIN_KEYS, SCOPE_TYPES, WIRED_CUSTOM_KEYS
from .jalali import fa_digits

PERIOD_DAY = "day"
PERIOD_MONTH = "month"
PERIOD_CHOICES = [(PERIOD_DAY, "در روز"), (PERIOD_MONTH, "در ماه")]


class Feature(models.Model):
    KIND_BUILTIN = "builtin"
    KIND_CONTENT = "content"
    KIND_CUSTOM = "custom"
    KIND_CHOICES = [
        (KIND_BUILTIN, "امکان اصلی اپ"),
        (KIND_CONTENT, "دسترسی به محتوا"),
        (KIND_CUSTOM, "امکان سفارشی"),
    ]

    key = models.SlugField(max_length=60, unique=True)
    name_fa = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    description_fa = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_CUSTOM)
    # Countable features can be capped per day or month in a plan; `unit` is
    # what one use is ("مقاله", "کارت").
    countable = models.BooleanField(default=False)
    unit_fa = models.CharField(max_length=30, blank=True)
    # Content features only: which content this one fences off.
    scope_type = models.CharField(max_length=30, choices=SCOPE_TYPES, blank=True)
    scope_value = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name_fa

    @property
    def is_wired(self):
        """False for a custom feature no code checks yet: it can sit in plans
        but opens and locks nothing until a developer connects it."""
        if self.kind == self.KIND_CUSTOM:
            return self.key in WIRED_CUSTOM_KEYS
        return self.kind == self.KIND_CONTENT or self.key in BUILTIN_KEYS


class Plan(models.Model):
    KIND_PLAN = "plan"
    KIND_PRODUCT = "product"
    KIND_CHOICES = [(KIND_PLAN, "پلن اشتراک"), (KIND_PRODUCT, "محصول تکی")]

    STATUS_ACTIVE = "active"
    STATUS_HIDDEN = "hidden"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "فعال و قابل خرید"),
        (STATUS_HIDDEN, "مخفی (فقط دستی یا با لینک)"),
        (STATUS_INACTIVE, "غیرفعال"),
    ]

    AUDIENCE_CHOICES = [("all", "همه"), ("pharmacy", "داروسازی"), ("medicine", "پزشکی")]

    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_PLAN)
    slug = models.SlugField(max_length=60, unique=True)
    name_fa = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    tagline_fa = models.CharField(max_length=160, blank=True)
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default="all")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    is_free = models.BooleanField(default=False)
    features = models.ManyToManyField(Feature, through="PlanFeature", related_name="plans")
    order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["is_free"], condition=Q(is_free=True), name="billing_one_free_plan"),
        ]

    def __str__(self):
        return self.name_fa


class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="plan_features")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="plan_features")
    # None = unlimited. Only meaningful on a countable feature.
    limit = models.PositiveIntegerField(null=True, blank=True)
    period = models.CharField(max_length=5, choices=PERIOD_CHOICES, default=PERIOD_DAY)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["plan", "feature"], name="billing_plan_feature_once")]

    def snapshot(self):
        limited = self.feature.countable and self.limit is not None
        return {"limit": self.limit if limited else None, "period": self.period if limited else ""}


class PlanPrice(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="prices")
    # None = permanent access (products).
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    price_toman = models.PositiveBigIntegerField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "duration_days", "id"]

    def __str__(self):
        return f"{self.plan} · {self.duration_label}"

    @property
    def duration_label(self):
        days = self.duration_days
        if days is None:
            return "دائمی"
        if days == 365:
            return "۱ ساله"
        if days % 30 == 0:
            return fa_digits(f"{days // 30} ماهه")
        return fa_digits(f"{days} روزه")


class DiscountCode(models.Model):
    code = models.CharField(max_length=40, unique=True)
    # Exactly one of the two is set.
    percent = models.PositiveSmallIntegerField(null=True, blank=True)
    amount_toman = models.PositiveBigIntegerField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    # Empty = valid on every plan and product.
    plans = models.ManyToManyField(Plan, blank=True, related_name="discount_codes")
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(percent__isnull=False) & Q(amount_toman__isnull=True))
                | (Q(percent__isnull=True) & Q(amount_toman__isnull=False)),
                name="billing_discount_one_kind",
            ),
            models.CheckConstraint(
                condition=Q(percent__isnull=True) | Q(percent__gte=1, percent__lte=100),
                name="billing_discount_percent_range",
            ),
        ]

    def __str__(self):
        return self.code


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار پرداخت"),
        (STATUS_PAID, "پرداخت‌شده"),
        (STATUS_FAILED, "ناموفق"),
        (STATUS_CANCELED, "لغوشده"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_orders")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="orders")
    price = models.ForeignKey(PlanPrice, on_delete=models.SET_NULL, null=True, related_name="orders")
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    amount_toman = models.PositiveBigIntegerField()
    discount = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    discount_toman = models.PositiveBigIntegerField(default=0)
    payable_toman = models.PositiveBigIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    gateway = models.CharField(max_length=20, blank=True)
    authority = models.CharField(max_length=64, null=True, blank=True, unique=True)
    ref_id = models.CharField(max_length=64, blank=True)
    card_pan = models.CharField(max_length=32, blank=True)
    error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-paid_at"], name="billing_order_paid_idx"),
            models.Index(fields=["user", "-created_at"], name="billing_order_user_idx"),
        ]

    def __str__(self):
        return f"Order<{self.pk}>"


class Entitlement(models.Model):
    SOURCE_PURCHASE = "purchase"
    SOURCE_ADMIN = "admin"
    SOURCE_CHOICES = [(SOURCE_PURCHASE, "خرید"), (SOURCE_ADMIN, "داده‌شده توسط ادمین")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entitlements")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="entitlements")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="entitlement")
    starts_at = models.DateTimeField(default=timezone.now)
    # None = permanent.
    ends_at = models.DateTimeField(null=True, blank=True)
    # {feature_key: {"limit": int | None, "period": "day" | "month" | ""}}
    # as the plan stood when this was bought or granted.
    features = models.JSONField(default=dict)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    note = models.CharField(max_length=255, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at", "-id"]
        indexes = [models.Index(fields=["user", "revoked_at", "ends_at"], name="billing_ent_user_idx")]

    def __str__(self):
        return f"{self.user_id} · {self.plan}"

    def is_active_at(self, when):
        return (
            self.revoked_at is None
            and self.starts_at <= when
            and (self.ends_at is None or self.ends_at > when)
        )


class UsageRecord(models.Model):
    """One counted use of a capped feature: the item used (an article, a
    question) once per period, so opening the same article twice in a day
    counts once."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    feature_key = models.CharField(max_length=60)
    period = models.CharField(max_length=5, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    item_key = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feature_key", "period", "period_start", "item_key"],
                name="billing_usage_once",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "feature_key", "period", "period_start"], name="billing_usage_idx"),
        ]


class AdminAction(models.Model):
    """Everything an operator does in the console, for the audit log."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    action = models.CharField(max_length=40)
    summary = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["target_user", "-created_at"], name="billing_action_user_idx")]


class BillingSettings(models.Model):
    """The console's gateway and switches: one row. An empty field (or no
    row) falls back to the environment variable of the same meaning, so the
    console only overrides what an operator has actually set."""

    GATEWAY_CHOICES = [("zarinpal", "زرین‌پال")]

    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, blank=True)
    zarinpal_merchant_id = models.CharField(max_length=64, blank=True)
    # None = use the environment's value.
    zarinpal_sandbox = models.BooleanField(null=True, blank=True)
    return_url = models.URLField(blank=True)
    enforcement_enabled = models.BooleanField(null=True, blank=True)
    sales_enabled = models.BooleanField(default=True)
    # Anyone opening the app gets a throwaway guest account, no sign-in --
    # for showing the content to a reviewer (sms.ir's site check).
    guest_access_enabled = models.BooleanField(default=False)
    last_test_at = models.DateTimeField(null=True, blank=True)
    last_test_ok = models.BooleanField(null=True, blank=True)
    last_test_message = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "billing settings"


class GuestAccount(models.Model):
    """Marks a throwaway account made for a visitor while guest access is on."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guest_account")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
