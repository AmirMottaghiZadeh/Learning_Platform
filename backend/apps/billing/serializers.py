from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Entitlement, Order, Plan, PlanPrice


class PlanPriceSerializer(serializers.ModelSerializer):
    duration_label = serializers.CharField(read_only=True)

    class Meta:
        model = PlanPrice
        fields = ["id", "duration_days", "duration_label", "price_toman", "compare_at_toman", "label_fa"]


class PlanFeatureItemSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    # how the plan words it, and whether its card lists it
    label_fa = serializers.CharField()
    is_listed = serializers.BooleanField()
    limit = serializers.IntegerField(allow_null=True)
    period = serializers.CharField()
    unit_fa = serializers.CharField()


class PlanSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    extra_lines = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id", "kind", "slug", "name_fa", "name_en", "tagline_fa", "description_fa", "badge_fa", "cta_label_fa",
            "extra_lines", "audience", "is_free", "prices", "features",
        ]

    @extend_schema_field(PlanPriceSerializer(many=True))
    def get_prices(self, plan):
        return PlanPriceSerializer([p for p in plan.prices.all() if p.is_active], many=True).data

    @extend_schema_field(PlanFeatureItemSerializer(many=True))
    def get_features(self, plan):
        rows = [
            {
                "key": pf.feature.key,
                "name_fa": pf.feature.name_fa,
                "label_fa": pf.label_fa,
                "is_listed": pf.is_listed,
                "unit_fa": pf.feature.unit_fa,
                **pf.snapshot(),
            }
            for pf in plan.plan_features.all()
            if pf.feature.is_active
        ]
        return PlanFeatureItemSerializer(rows, many=True).data


class CatalogSerializer(serializers.Serializer):
    free = PlanSerializer(allow_null=True)
    plans = PlanSerializer(many=True)
    products = PlanSerializer(many=True)


class MyFeatureSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    limit = serializers.IntegerField(allow_null=True)
    period = serializers.CharField()
    used = serializers.IntegerField()


class MyEntitlementSerializer(serializers.ModelSerializer):
    plan_name_fa = serializers.CharField(source="plan.name_fa")
    plan_kind = serializers.CharField(source="plan.kind")
    days_left = serializers.SerializerMethodField()

    class Meta:
        model = Entitlement
        fields = ["id", "plan_name_fa", "plan_kind", "source", "starts_at", "ends_at", "days_left"]

    def get_days_left(self, ent) -> int | None:
        if ent.ends_at is None:
            return None
        return max(0, (ent.ends_at - timezone.now()).days)


class MyAccessSerializer(serializers.Serializer):
    enforced = serializers.BooleanField()
    features = MyFeatureSerializer(many=True)
    entitlements = MyEntitlementSerializer(many=True)


class PurchaseRequestSerializer(serializers.Serializer):
    price_id = serializers.IntegerField()
    discount_code = serializers.CharField(required=False, allow_blank=True, max_length=40, default="")


class QuoteSerializer(serializers.Serializer):
    amount_toman = serializers.IntegerField()
    discount_toman = serializers.IntegerField()
    payable_toman = serializers.IntegerField()


class CheckoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    payment_url = serializers.CharField(allow_blank=True)


class OrderSerializer(serializers.ModelSerializer):
    plan_name_fa = serializers.CharField(source="plan.name_fa")

    class Meta:
        model = Order
        fields = [
            "id", "plan_name_fa", "duration_days", "amount_toman", "discount_toman",
            "payable_toman", "status", "ref_id", "created_at", "paid_at",
        ]
