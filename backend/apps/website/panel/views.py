"""Panel pages: sign-in, dashboard, statistics, SEO, settings, staff, activity, search."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import LearnerProfile
from apps.accounts.phone import looks_like_phone, normalize_phone

from .. import services
from ..models import (
    ActivityLog, Announcement, Comment, ContactMessage, DailyStat, DownloadLink, Media, Page, Post, Redirect, SiteSettings, StaffRole, VisitorDay,
)
from ..permissions import can, panel_required, role_of
from . import forms
from .ui import jalali_format, log, paginate, render_panel

User = get_user_model()


# -- sign-in -----------------------------------------------------------------------

def login_view(request):
    """The admin's one sign-in (apps.manage) took this page's place."""
    from apps.manage.views import to_login

    return to_login(request)


@require_POST
def logout_view(request):
    from apps.manage.views import logout_view as manage_logout

    return manage_logout(request)


# -- dashboard -----------------------------------------------------------------------

def _series(kind, days, key=None):
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    qs = DailyStat.objects.filter(kind=kind, day__gte=start)
    if key is not None:
        qs = qs.filter(key=key)
    by_day = dict(qs.values_list("day").annotate(n=Sum("count")).values_list("day", "n"))
    return [(start + timedelta(days=i), by_day.get(start + timedelta(days=i), 0)) for i in range(days)]


def _unique_series(days):
    """Distinct visitor IPs per day, oldest first."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    by_day = dict(VisitorDay.objects.filter(day__gte=start).values_list("day").annotate(n=Count("id")).values_list("day", "n"))
    return [(start + timedelta(days=i), by_day.get(start + timedelta(days=i), 0)) for i in range(days)]


def _unique_between(first, last):
    """Distinct IPs over a span of days -- a visitor on three days counts once."""
    return VisitorDay.objects.filter(day__range=(first, last)).values("ip_hash").distinct().count()


def _paths(values, width=560, height=150, pad=10, top=None):
    """(line path, area path) for a list of numbers drawn in a width x height box."""
    top = top or (max(values) if values and max(values) else 1)
    step = (width - 2 * pad) / max(len(values) - 1, 1)
    pts = [(pad + i * step, height - pad - (v / top) * (height - 2 * pad)) for i, v in enumerate(values)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = f"{line} L{pts[-1][0]:.1f} {height} L{pts[0][0]:.1f} {height}Z"
    return line, area


def _delta(now, before):
    if not before:
        return None
    return round(100 * (now - before) / before)


@panel_required("dashboard.view")
def dashboard(request):
    from apps.billing.models import Entitlement, Order

    days = 30
    views = _series(DailyStat.VIEW, days)
    prev_start = timezone.localdate() - timedelta(days=2 * days - 1)
    prev_end = timezone.localdate() - timedelta(days=days)
    prev_views = DailyStat.objects.filter(kind=DailyStat.VIEW, day__range=(prev_start, prev_end)).aggregate(n=Sum("count"))["n"] or 0
    views_total = sum(n for _, n in views)
    today = timezone.localdate()
    uniques_total = _unique_between(today - timedelta(days=days - 1), today)
    prev_uniques = _unique_between(prev_start, prev_end)
    line, area = _paths([n for _, n in views])
    downloads = _series(DailyStat.DOWNLOAD, days)
    subs = _series(DailyStat.SUBSCRIBE, days)
    by_store = list(DailyStat.objects.filter(kind=DailyStat.DOWNLOAD, day__gte=timezone.localdate() - timedelta(days=days - 1))
                    .values("key").annotate(n=Sum("count")).order_by("-n"))
    store_names = dict(DownloadLink.STORES)
    top = max([r["n"] for r in by_store] or [1])
    platforms = [{"name": store_names.get(r["key"], r["key"]), "n": r["n"], "pct": round(100 * r["n"] / top)} for r in by_store[:5]]

    ctx = {
        "views_total": views_total, "views_delta": _delta(views_total, prev_views),
        "uniques_total": uniques_total, "uniques_delta": _delta(uniques_total, prev_uniques), "chart_line": line, "chart_area": area,
        "chart_max": max([n for _, n in views] or [0]), "chart_first": jalali_format(views[0][0]), "chart_last": jalali_format(views[-1][0]),
        "downloads_total": sum(n for _, n in downloads), "subscribers_new": sum(n for _, n in subs),
        "platforms": platforms, "show_sales": can(request.user, "orders.view"),
        "posts_total": Post.objects.filter(status=Post.PUBLISHED).count(), "today": jalali_format(timezone.localdate()),
    }
    posts = Post.objects.select_related("category", "author")
    if not can(request.user, "post.view_all"):
        posts = posts.filter(author=request.user)
    ctx["recent_posts"] = posts.order_by("-updated_at")[:6]
    tasks = []
    if can(request.user, "comment.moderate"):
        n = Comment.objects.filter(status=Comment.PENDING).count()
        if n:
            tasks.append((f"{n} نظر در انتظار تأیید", reverse("panel:comments") + "?status=pending", "warn"))
    if can(request.user, "contact.view"):
        n = ContactMessage.objects.filter(status=ContactMessage.NEW).count()
        if n:
            tasks.append((f"{n} پیام تماس خوانده‌نشده", reverse("panel:contact"), "warn"))
    if can(request.user, "post.view_all"):
        n = Post.objects.filter(status=Post.REVIEW).count()
        if n:
            tasks.append((f"{n} مطلب در انتظار بازبینی", reverse("panel:posts") + "?status=review", "warn"))
        n = Post.objects.filter(status=Post.SCHEDULED, published_at__gt=timezone.now(), published_at__lte=timezone.now() + timedelta(days=7)).count()
        if n:
            tasks.append((f"{n} مطلب برای ۷ روز آینده زمان‌بندی شده", reverse("panel:posts") + "?status=scheduled", "info"))
    if ctx["show_sales"]:
        since = timezone.now() - timedelta(hours=24)
        n = Order.objects.filter(status=Order.STATUS_FAILED, created_at__gte=since).count()
        if n:
            tasks.append((f"{n} پرداخت ناموفق در ۲۴ ساعت اخیر", reverse("panel:orders") + "?status=failed", "warn"))
        paid = Order.objects.filter(status=Order.STATUS_PAID, paid_at__gte=timezone.now() - timedelta(days=days))
        paid_prev = Order.objects.filter(status=Order.STATUS_PAID, paid_at__gte=timezone.now() - timedelta(days=2 * days), paid_at__lt=timezone.now() - timedelta(days=days))
        revenue = paid.aggregate(n=Sum("payable_toman"))["n"] or 0
        ctx.update(
            revenue=revenue, revenue_delta=_delta(revenue, paid_prev.aggregate(n=Sum("payable_toman"))["n"] or 0), orders_paid=paid.count(),
            active_subs=Entitlement.objects.filter(revoked_at__isnull=True, starts_at__lte=timezone.now()).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).values("user").distinct().count(),
        )
    ctx["tasks"] = tasks
    return render_panel(request, "panel/dashboard.html", ctx, active="dash")


# -- statistics ------------------------------------------------------------------------

@panel_required("dashboard.view")
def stats(request):
    days = {"7": 7, "30": 30, "90": 90}.get(request.GET.get("range"), 30)
    since = timezone.localdate() - timedelta(days=days - 1)
    views = _series(DailyStat.VIEW, days)
    uniques = _unique_series(days)
    top = max([n for _, n in views] + [1])
    line, area = _paths([n for _, n in views], top=top)
    uline, _ = _paths([n for _, n in uniques], top=top)
    unique_by_day = dict(uniques)
    post_rows = list(DailyStat.objects.filter(kind=DailyStat.POST, day__gte=since).values("key").annotate(n=Sum("count")).order_by("-n")[:10])
    titles = dict(Post.objects.filter(pk__in=[r["key"] for r in post_rows if r["key"].isdigit()]).values_list("pk", "title"))
    top_posts = [{"title": titles.get(int(r["key"]), "(حذف‌شده)"), "n": r["n"], "pk": int(r["key"])} for r in post_rows if r["key"].isdigit()]
    top_pages = list(DailyStat.objects.filter(kind=DailyStat.VIEW, day__gte=since).values("key").annotate(n=Sum("count")).order_by("-n")[:10])
    downloads_by_day = dict(_series(DailyStat.DOWNLOAD, days))
    table = [{"day": jalali_format(d), "views": n, "uniques": unique_by_day.get(d, 0), "downloads": downloads_by_day.get(d, 0)} for d, n in reversed(views[-14:])]
    return render_panel(request, "panel/stats.html", {
        "range": str(days), "total": sum(n for _, n in views), "line": line, "area": area, "uline": uline,
        "uniques": _unique_between(since, timezone.localdate()), "top_posts": top_posts, "top_pages": top_pages, "table": table,
        "downloads": sum(n for _, n in _series(DailyStat.DOWNLOAD, days)), "subs": sum(n for _, n in _series(DailyStat.SUBSCRIBE, days)),
        "contacts": sum(n for _, n in _series(DailyStat.CONTACT, days)), "signins": sum(n for _, n in _series(DailyStat.SIGNIN, days)),
    }, active="stats")


# -- SEO -----------------------------------------------------------------------------------

@panel_required("seo.manage")
def seo(request):
    live = Post.objects.live()
    issues = []
    for post in live.select_related("cover"):
        problems = []
        if not post.seo_description and not post.excerpt:
            problems.append("بدون توضیح سئو یا خلاصه")
        elif len(post.meta_description) < 70:
            problems.append("توضیح سئو کوتاه است")
        if len(post.meta_title) > 65:
            problems.append("عنوان بلند است (بیش از ۶۵ نویسه)")
        if not post.cover_id:
            problems.append("بدون تصویر شاخص")
        elif not post.cover.alt:
            problems.append("تصویر شاخص بدون متن جایگزین")
        if problems:
            issues.append((post, problems))
    return render_panel(request, "panel/seo.html", {
        "issues": issues[:30], "issue_count": len(issues), "post_count": live.count(), "site": SiteSettings.get(),
        "redirect_count": Redirect.objects.count(),
        "noindex_pages": Page.objects.filter(noindex=True).count() + Post.objects.filter(noindex=True).count(),
    }, active="seo")


# -- settings -----------------------------------------------------------------------------

@panel_required("*")
def settings_view(request):
    tabs = forms.SETTINGS_TABS
    key = request.GET.get("tab") or tabs[0][0]
    tab = next((t for t in tabs if t[0] == key), tabs[0])
    fields = [f for f in tab[2] if f != "analytics_head" or request.user.is_superuser]
    form_class = forms.settings_form_class(fields)
    instance = SiteSettings.get()
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        log(request, "settings", instance, detail=tab[1])
        messages.success(request, "تنظیمات ذخیره شد.")
        return redirect(f"{reverse('panel:settings')}?tab={tab[0]}")
    return render_panel(request, "panel/settings.html", {
        "form": form, "tabs": [(k, label) for k, label, _ in tabs], "tab": tab[0], "tab_label": tab[1],
    }, active="settings")


# -- staff ---------------------------------------------------------------------------------

def _find_user(identifier):
    identifier = identifier.strip()
    if looks_like_phone(identifier):
        profile = LearnerProfile.objects.select_related("user").filter(phone=normalize_phone(identifier)).first()
        return profile.user if profile else None
    return User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()


@panel_required("*")
def staff(request):
    form = forms.StaffAddForm(request.POST or None)
    if request.method == "POST" and request.POST.get("action") == "add" and form.is_valid():
        user = _find_user(form.cleaned_data["identifier"])
        if user is None:
            form.add_error("identifier", "کاربری با این مشخصات پیدا نشد؛ کاربر باید اول در اپ ثبت‌نام کند.")
        else:
            StaffRole.objects.update_or_create(user=user, defaults={"role": form.cleaned_data["role"]})
            log(request, "staff_add", user, detail=form.cleaned_data["role"])
            messages.success(request, "نقش ثبت شد.")
            return redirect("panel:staff")
    rows = StaffRole.objects.select_related("user", "user__learner_profile").order_by("created_at")
    supers = User.objects.filter(is_superuser=True, is_active=True).exclude(pk__in=rows.values("user_id"))
    return render_panel(request, "panel/staff.html", {
        "rows": rows, "supers": supers, "form": form, "roles": StaffRole.ROLE_CHOICES,
    }, active="staff")


@require_POST
@panel_required("*")
def staff_update(request, pk):
    row = get_object_or_404(StaffRole, pk=pk)
    if row.user_id == request.user.id:
        messages.error(request, "نقش خودتان را نمی‌توانید تغییر دهید.")
        return redirect("panel:staff")
    if request.POST.get("action") == "remove":
        log(request, "staff_remove", row.user)
        row.delete()
    elif request.POST.get("role") in dict(StaffRole.ROLE_CHOICES):
        row.role = request.POST["role"]
        row.save(update_fields=["role"])
        log(request, "staff_role", row.user, detail=row.role)
    return redirect("panel:staff")


@panel_required("*")
def activity(request):
    qs = ActivityLog.objects.all()
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(user_label__icontains=q) | Q(object_repr__icontains=q) | Q(action__icontains=q))
    return render_panel(request, "panel/activity.html", {"page": paginate(request, qs, 40), "q": q}, active="activity")


# -- global search --------------------------------------------------------------------------

@panel_required(None)
def search(request):
    return JsonResponse({"results": search_items(request.user, (request.GET.get("q") or "").strip())})


def search_items(user, q):
    """Posts, pages, site announcements and media whose title has `q`, as far
    as `user`'s role may open them -- also what the admin's command bar finds."""
    out = []
    if len(q) < 2:
        return out
    posts = Post.objects.filter(title__icontains=q)
    if not can(user, "post.view_all"):
        posts = posts.filter(author=user)
    if can(user, "post.create"):
        out += [{"type": "مطلب", "label": p.title, "url": reverse("panel:post_edit", args=[p.pk])} for p in posts[:6]]
    if can(user, "page.manage"):
        out += [{"type": "برگه", "label": p.title, "url": reverse("panel:pages_edit", args=[p.pk])} for p in Page.objects.filter(title__icontains=q)[:4]]
    if can(user, "announcement.manage"):
        out += [{"type": "اطلاعیهٔ سایت", "label": a.title, "url": reverse("panel:announcements_edit", args=[a.pk])} for a in Announcement.objects.filter(title__icontains=q)[:4]]
    if can(user, "media.upload"):
        out += [{"type": "رسانه", "label": m.title or m.filename, "url": reverse("panel:media_edit", args=[m.pk])} for m in Media.objects.filter(Q(title__icontains=q) | Q(filename__icontains=q))[:4]]
    return out
