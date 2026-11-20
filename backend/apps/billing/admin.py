from django.contrib import admin

from .models import AdminAction, DiscountCode, Entitlement, Feature, Order, Plan, PlanFeature, PlanPrice


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 0


class PlanPriceInline(admin.TabularInline):
    model = PlanPrice
    extra = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name_fa", "kind", "status", "is_free", "order"]
    inlines = [PlanFeatureInline, PlanPriceInline]


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["key", "name_fa", "kind", "countable", "is_active"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "plan", "payable_toman", "status", "created_at", "paid_at"]
    list_filter = ["status", "gateway"]
    raw_id_fields = ["user"]


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "source", "starts_at", "ends_at", "revoked_at"]
    raw_id_fields = ["user", "order", "granted_by", "revoked_by"]


admin.site.register(DiscountCode)
admin.site.register(AdminAction)
