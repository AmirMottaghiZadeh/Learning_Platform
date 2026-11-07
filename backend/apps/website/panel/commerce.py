"""Plans, orders and subscriptions as the panel shows them. They are read
from `apps.billing`; editing prices and plans happens in the sales console
(/ops/), which every row here links to."""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from apps.billing.models import DiscountCode, Entitlement, Order, Plan

from ..models import SiteSettings
from ..permissions import panel_required
from .ui import paginate, render_panel


@panel_required("orders.view")
def plans(request):
    rows = []
    featured = SiteSettings.get().featured_plan_slug
    for plan in Plan.objects.prefetch_related("prices").annotate(feature_count=Count("plan_features", distinct=True)):
        rows.append({"plan": plan, "prices": [p for p in plan.prices.all() if p.is_active], "featured": plan.slug == featured,
                     "edit": reverse("console:plan_basics", args=[plan.pk])})
    return render_panel(request, "panel/plans.html", {"rows": rows, "new_url": reverse("console:plan_new"), "ops_url": reverse("console:home")}, active="plans")


@panel_required("orders.view")
def orders(request):
    qs = Order.objects.select_related("plan", "user", "user__learner_profile").order_by("-created_at")
    status = request.GET.get("status", "")
    if status in dict(Order.STATUS_CHOICES):
        qs = qs.filter(status=status)
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(user__learner_profile__phone__icontains=q) | Q(ref_id__icontains=q) | Q(plan__name_fa__icontains=q) | Q(deleted_user_label__icontains=q))
    month = timezone.now() - timedelta(days=30)
    paid = Order.objects.filter(status=Order.STATUS_PAID)
    summary = {
        "revenue_30": paid.filter(paid_at__gte=month).aggregate(n=Sum("payable_toman"))["n"] or 0,
        "orders_30": paid.filter(paid_at__gte=month).count(),
        "failed_30": Order.objects.filter(status=Order.STATUS_FAILED, created_at__gte=month).count(),
        "pending": Order.objects.filter(status=Order.STATUS_PENDING).count(),
    }
    counts = dict(Order.objects.values_list("status").annotate(n=Count("id")))
    tabs = [("", "همه", sum(counts.values()))] + [(k, label, counts.get(k, 0)) for k, label in Order.STATUS_CHOICES]
    return render_panel(request, "panel/orders.html", {"page": paginate(request, qs, 25), "status": status, "q": q, "summary": summary, "tabs": tabs, "sales_url": reverse("console:sales")}, active="orders")


@panel_required("orders.view")
def subscriptions(request):
    now = timezone.now()
    active = Entitlement.objects.filter(revoked_at__isnull=True, starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
    by_plan = list(active.values("plan__name_fa").annotate(n=Count("user", distinct=True)).order_by("-n"))
    expiring = active.filter(ends_at__isnull=False, ends_at__lte=now + timedelta(days=7)).select_related("plan", "user", "user__learner_profile").order_by("ends_at")[:15]
    return render_panel(request, "panel/subscriptions.html", {
        "by_plan": by_plan, "total": active.values("user").distinct().count(), "expiring": expiring,
        "discounts": DiscountCode.objects.order_by("-created_at")[:20], "discounts_url": reverse("console:discounts"), "access_url": reverse("console:access"),
    }, active="subs")
