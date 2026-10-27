"""The admin's own pages: one sign-in for every tool, the home that gathers
what needs doing today, the merged activity log, and the command bar's
search. The tools themselves (sales, site, data quality) keep their views
and mount under /manage/ (config/urls.py)."""

from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, get_user_model, login, logout
from django.core.cache import caches
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

from apps.accounts.models import SecurityAuditEvent, UserSession
from apps.accounts.services import record_security_event
from apps.billing import jalali

from . import access

User = get_user_model()
LOGIN_MAX_FAILURES = 8
LOGIN_LOCKOUT_SECONDS = 15 * 60
# Python's weekday(): Monday is 0.
WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
_LATIN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def login_url(next_path=""):
    url = reverse("manage:login")
    return f"{url}?{REDIRECT_FIELD_NAME}={next_path}" if next_path else url


def manage_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not access.can_enter(request.user):
            return redirect(login_url(request.get_full_path()))
        return view(request, *args, **kwargs)

    return wrapper


def _url(name, *args, query=""):
    try:
        return reverse(name, args=args) + query
    except NoReverseMatch:
        return ""


def _ago(when):
    if not when:
        return ""
    text = timesince(when, timezone.now()).split(",")[0]
    return jalali.fa_digits(f"{text} پیش")


def today_label(day=None):
    day = day or timezone.localdate()
    return f"{WEEKDAYS[day.weekday()]} {jalali.format_date(day, with_month_name=True)}"


# -- sign in ------------------------------------------------------------------

def client_ip(request):
    """The caller's address. Behind the platform's proxy REMOTE_ADDR is the
    proxy; it appends the address it saw to X-Forwarded-For, so the LAST
    entry is the one a client cannot forge."""
    forwarded = [p.strip() for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]
    return forwarded[-1] if forwarded else request.META.get("REMOTE_ADDR", "")


def _safe_next(request):
    nxt = request.POST.get(REDIRECT_FIELD_NAME) or request.GET.get(REDIRECT_FIELD_NAME) or ""
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return nxt
    return ""


def login_view(request):
    if access.can_enter(request.user):
        return redirect(_safe_next(request) or "manage:home")
    throttle = caches["throttle"]
    key = f"manage-login:{client_ip(request)}"
    error, identifier = "", ""
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()[:150]
        if throttle.get(key, 0) >= LOGIN_MAX_FAILURES:
            error = "تلاش‌های ناموفق زیاد بود؛ ۱۵ دقیقهٔ دیگر دوباره امتحان کنید."
        else:
            user = authenticate(request, username=identifier, password=request.POST.get("password") or "")
            if user is not None and access.can_enter(user):
                throttle.delete(key)
                login(request, user)
                record_security_event(
                    SecurityAuditEvent.LOGIN_SUCCEEDED, user=user, request=request, metadata={"surface": "manage"}
                )
                if access.has_site_role(user):
                    from apps.website.panel.ui import log

                    log(request, "login")
                return redirect(_safe_next(request) or "manage:home")
            throttle.set(key, throttle.get(key, 0) + 1, LOGIN_LOCKOUT_SECONDS)
            record_security_event(
                SecurityAuditEvent.LOGIN_FAILED, user=user, request=request,
                metadata={"surface": "manage", "username": identifier},
            )
            error = "نام کاربری یا رمز درست نیست، یا این حساب به مدیریت دسترسی ندارد."
    return render(request, "manage/login.html", {"error": error, "identifier": identifier, "next": _safe_next(request)})


@require_POST
def logout_view(request):
    if access.has_site_role(request.user):
        from apps.website.panel.ui import log

        log(request, "logout")
    logout(request)
    return redirect("manage:login")


def to_login(request):
    """What the tools' old sign-in pages do now: send to the one sign-in."""
    return redirect(login_url(_safe_next(request)))


# -- home ---------------------------------------------------------------------

def _review_column(user):
    from apps.data_quality_center.labels import FIELD_FA
    from apps.data_quality_center.models import SectionEditRequest as R

    if access.is_super(user):
        qs = R.objects.filter(status=R.STATUS_PENDING).order_by("submitted_at", "pk")
        title, link_label = "بازبینی داده‌ها", "میز بازبینی"
        items = [{
            "title": f"{r.ingredient_name} — {FIELD_FA.get(r.field, r.field)}",
            "meta": f"{r.requested_by_username or '—'} · {_ago(r.submitted_at)}",
            "url": _url("data_quality_center:review", query=f"?id={r.pk}"), "go": "دیدن تفاوت و تصمیم",
        } for r in qs[:3]]
        more_url = _url("data_quality_center:review")
    else:
        qs = R.objects.filter(requested_by=user, status=R.STATUS_CHANGES_REQUESTED).order_by("-reviewed_at")
        title, link_label = "اصلاح‌های خواسته‌شده", "درخواست‌های من"
        items = [{
            "title": f"{r.ingredient_name} — {FIELD_FA.get(r.field, r.field)}",
            "meta": f"{r.reviewed_by_username or '—'} · {_ago(r.reviewed_at)}",
            "url": _url("data_quality_center:mine"), "go": "اصلاح",
        } for r in qs[:3]]
        more_url = _url("data_quality_center:mine")
    count = qs.count()
    return {"key": "data", "tone": "hi", "title": title, "count": count, "items": items,
            "more": count - len(items), "more_url": more_url, "more_label": link_label}


def _inbox_column(user):
    from apps.website.models import Comment, ContactMessage
    from apps.website.permissions import can

    items, count = [], 0
    if can(user, "comment.moderate"):
        pending = Comment.objects.filter(status=Comment.PENDING).select_related("post").order_by("created_at")
        count += pending.count()
        for c in pending[:2]:
            items.append({
                "title": c.body[:120], "meta": f"نظر روی «{c.post.title[:40]}» · {_ago(c.created_at)}",
                "comment": c.pk, "url": _url("panel:comments", query="?status=pending"),
            })
    if can(user, "contact.view"):
        new = ContactMessage.objects.filter(status=ContactMessage.NEW).order_by("-created_at")
        count += new.count()
        for m in new[: max(0, 3 - len(items))]:
            items.append({
                "title": (m.subject or m.message)[:120], "meta": f"پیام تماس از {m.name} · {_ago(m.created_at)}",
                "url": _url("panel:contact"), "go": "خواندن و پاسخ",
            })
    if not (can(user, "comment.moderate") or can(user, "contact.view")):
        return None
    return {"key": "inbox", "tone": "info", "title": "نظرها و پیام‌ها", "count": count, "items": items,
            "more": count - len(items), "more_url": _url("panel:comments"), "more_label": "همهٔ نظرها"}


def _sales_column(user, now):
    from apps.billing import config
    from apps.billing.models import Entitlement, Order

    items = []
    failed = Order.objects.filter(status=Order.STATUS_FAILED, created_at__date=timezone.localdate()).select_related("plan")
    n_failed = failed.count()
    if n_failed:
        last = failed.order_by("-created_at").first()
        items.append({
            "title": f"{jalali.fa_digits(n_failed)} پرداخت ناموفق امروز",
            "meta": f"آخری: {last.plan.name_fa} · {last.gateway or 'درگاه'} · {_ago(last.created_at)}",
            "url": _url("panel:orders", query="?status=failed"), "go": "دیدن سفارش‌ها",
        })
    expiring = Entitlement.objects.filter(
        revoked_at__isnull=True, ends_at__gt=now, ends_at__lte=now + timedelta(days=7)
    ).values("user").distinct().count()
    if expiring:
        items.append({
            "title": f"{jalali.fa_digits(expiring)} اشتراک تا ۷ روز دیگر تمام می‌شود",
            "meta": "کسانی که هنوز تمدید نکرده‌اند",
            "url": _url("panel:subscriptions"), "go": "دیدن فهرست",
        })
    guest = config.current().guest_access
    return {"key": "sales", "tone": "bad", "title": "فروش و حساب‌ها", "count": len(items), "items": items,
            "more": 0, "guest": guest, "guest_url": _url("console:access")}


def _daily(qs, field, value_field=None, days=14):
    start = timezone.localdate() - timedelta(days=days - 1)
    rows = qs.filter(**{f"{field}__date__gte": start}).annotate(d=TruncDate(field)).values("d")
    rows = rows.annotate(n=Sum(value_field) if value_field else Count("id"))
    by_day = {r["d"]: r["n"] or 0 for r in rows}
    return [by_day.get(start + timedelta(days=i), 0) for i in range(days)]


def _spark(values, width=96, height=28):
    """A sparkline's polyline points from oldest-first values: the oldest
    on the right, the newest on the left (RTL)."""
    if not values or max(values) == 0:
        return ""
    top, n = max(values), len(values)
    step = width / max(1, n - 1)
    return " ".join(
        f"{width - i * step:.1f},{height - 3 - (v / top) * (height - 6):.1f}" for i, v in enumerate(values)
    )


def _tiles(user, now):
    tiles = []
    if access.is_super(user):
        active = UserSession.objects.filter(last_used_at__gte=now - timedelta(days=7)).values("user").distinct().count()
        joined = User.objects.filter(date_joined__gte=now - timedelta(days=7)).count()
        tiles.append({"label": "کاربران", "value": jalali.fa_digits(f"{active:,}").replace(",", "٬"),
                      "sub": f"فعال در ۷ روز · {jalali.fa_digits(joined)} ثبت‌نام تازه", "url": _url("console:users")})
        from apps.billing.models import Order

        paid = Order.objects.filter(status=Order.STATUS_PAID)
        month = paid.filter(paid_at__date__gte=jalali.month_start(timezone.localdate()))
        total = month.aggregate(n=Sum("payable_toman"))["n"] or 0
        tiles.append({
            "label": "فروش", "value": jalali.fa_digits(f"{total / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", "٫")),
            "unit": "میلیون تومان", "sub": f"این ماه · {jalali.fa_digits(month.count())} سفارش",
            "spark": _spark(_daily(paid, "paid_at", "payable_toman")), "url": _url("console:sales"),
        })
    from apps.website.permissions import can

    if can(user, "download.manage") or access.is_super(user):
        from apps.website.models import AppRelease

        latest = AppRelease.objects.filter(is_published=True).order_by("-released_at", "-id").first()
        sub = jalali.format_date(latest.released_at, with_month_name=True) if latest else "هنوز نسخه‌ای ثبت نشده"
        if access.is_super(user):
            from apps.announcements.models import AppAnnouncement

            live = sum(1 for a in AppAnnouncement.objects.filter(is_published=True) if a.state_at(now) == AppAnnouncement.STATE_ACTIVE)
            sub = f"{jalali.fa_digits(live)} اعلان فعال · {sub}"
        tiles.append({"label": "اپ", "value": jalali.fa_digits(latest.version) if latest else "—",
                      "unit": "آخرین نسخه" if latest else "", "sub": sub,
                      "url": _url("app_admin:announcements") if access.is_super(user) else _url("panel:releases")})
    if can(user, "dashboard.view"):
        from apps.website.models import DailyStat

        start = timezone.localdate() - timedelta(days=13)
        rows = DailyStat.objects.filter(kind=DailyStat.VIEW, day__gte=start).values("day").annotate(n=Sum("count"))
        by_day = {r["day"]: r["n"] for r in rows}
        series = [by_day.get(start + timedelta(days=i), 0) for i in range(14)]
        downloads = DailyStat.objects.filter(kind=DailyStat.DOWNLOAD, day=timezone.localdate()).aggregate(n=Sum("count"))["n"] or 0
        tiles.append({"label": "سایت", "value": jalali.fa_digits(series[-1]), "unit": "بازدید امروز",
                      "sub": f"{jalali.fa_digits(downloads)} دانلود اپ امروز", "spark": _spark(series),
                      "url": _url("panel:dashboard")})
    if access.is_operator(user):
        from apps.data_quality_center.models import SectionEdit, SectionEditRequest as R

        month_start = jalali.month_start(timezone.localdate())
        approved = SectionEdit.objects.filter(created_at__date__gte=month_start).count()
        open_n = R.objects.filter(status=R.STATUS_PENDING).count()
        tiles.append({"label": "کیفیت داده", "value": jalali.fa_digits(approved), "unit": "ویرایش اعمال‌شده این ماه",
                      "sub": f"{jalali.fa_digits(open_n)} در انتظار تأیید", "url": _url("data_quality_center:queue")})
    return tiles


@manage_required
def home(request):
    user, now = request.user, timezone.now()
    columns = []
    if access.is_operator(user):
        columns.append(_review_column(user))
    inbox = _inbox_column(user)
    if inbox:
        columns.append(inbox)
    if access.is_super(user):
        columns.append(_sales_column(user, now))
    waiting = sum(c["count"] for c in columns)
    urgent = sum(c["count"] for c in columns if c["key"] in ("sales", "data"))
    return render(request, "manage/home.html", {
        "today": today_label(), "columns": columns, "waiting": waiting, "urgent": urgent,
        "tiles": _tiles(user, now),
        "events": activity_rows(user, limit=6, since=now - timedelta(hours=24)) if _may_see_activity(user) else [],
    })


# -- activity -----------------------------------------------------------------

# What the site's ActivityLog codes mean, for the merged log.
SITE_ACTIONS = {
    "login": "ورود به مدیریت", "logout": "خروج از مدیریت", "create": "ساخت", "update": "ویرایش", "delete": "حذف",
    "upload": "بارگذاری", "duplicate": "تکثیر", "restore": "برگرداندن نسخهٔ", "settings": "تغییر تنظیمات سایت",
    "staff_add": "دادن نقش به", "staff_role": "تغییر نقش", "staff_remove": "برداشتن نقش", "export_subscribers": "خروجی گرفتن از خبرنامه",
    "comment_reply": "پاسخ به نظر", "comment_approve": "انتشار نظر", "comment_trash": "رد نظر", "comment_spam": "هرزنامه دانستن نظر",
    "comment_pending": "برگرداندن نظر به انتظار", "comment_delete": "حذف نظر",
    "bulk_publish": "انتشار گروهی", "bulk_draft": "پیش‌نویس کردن گروهی", "bulk_archive": "بایگانی گروهی",
    "bulk_feature": "ویژه کردن گروهی", "bulk_delete": "حذف گروهی",
}
SITE_OBJECTS = {
    "Post": "مطلب", "Page": "برگه", "Category": "دسته", "Tag": "برچسب", "Media": "رسانه", "Announcement": "اطلاعیهٔ سایت",
    "AppRelease": "نسخهٔ اپ", "DownloadLink": "پیوند دانلود", "MenuItem": "منو", "ContentBlock": "بلوک صفحهٔ اصلی",
    "Redirect": "تغییر مسیر", "Comment": "نظر", "Subscriber": "مشترک خبرنامه", "StaffRole": "نقش", "User": "کاربر",
}


def _site_action(entry):
    what = SITE_ACTIONS.get(entry.action, entry.action)
    kind = SITE_OBJECTS.get(entry.object_type, entry.object_type)
    if entry.object_repr:
        return f"{what} {kind} «{entry.object_repr}»".replace("  ", " ")
    return what

def _may_see_activity(user):
    return access.is_super(user) or access.site_admin(user)


def activity_rows(user, *, limit=40, offset=0, source="", q="", since=None):
    """The site's ActivityLog and the sales tools' AdminAction, newest first,
    as far as this user may see them."""
    from apps.billing.models import AdminAction
    from apps.website.models import ActivityLog

    take = offset + limit
    rows = []
    if access.site_admin(user) and source in ("", "site"):
        qs = ActivityLog.objects.all()
        if q:
            qs = qs.filter(Q(user_label__icontains=q) | Q(object_repr__icontains=q) | Q(action__icontains=q))
        if since:
            qs = qs.filter(created_at__gte=since)
        rows += [{"at": a.created_at, "who": a.user_label or "—", "what": _site_action(a),
                  "action": a.action, "detail": a.detail, "source": "سایت", "tone": "info"} for a in qs.order_by("-created_at")[:take]]
    if access.is_super(user) and source in ("", "sales"):
        qs = AdminAction.objects.select_related("actor", "target_user")
        if q:
            qs = qs.filter(Q(summary__icontains=q) | Q(action__icontains=q) | Q(actor__username__icontains=q))
        if since:
            qs = qs.filter(created_at__gte=since)
        rows += [{"at": a.created_at, "who": a.actor.get_username() if a.actor else "—", "what": a.summary,
                  "action": a.action, "detail": a.target_user.get_username() if a.target_user else "",
                  "source": "فروش و کاربران", "tone": "hi"} for a in qs.order_by("-created_at")[:take]]
    rows.sort(key=lambda r: r["at"], reverse=True)
    for r in rows:
        local = timezone.localtime(r["at"])
        r["when"] = jalali.fa_digits(local.strftime("%H:%M"))
        r["date"] = jalali.format_date(local.date())
    return rows[offset:take]


@manage_required
def activity(request):
    if not _may_see_activity(request.user):
        return render(request, "manage/forbidden.html", status=403)
    source = request.GET.get("source", "")
    if source not in ("", "site", "sales"):
        source = ""
    q = (request.GET.get("q") or "").strip()[:80]
    try:
        page = max(1, int(request.GET.get("page") or 1))
    except ValueError:
        page = 1
    per = 40
    rows = activity_rows(request.user, limit=per + 1, offset=(page - 1) * per, source=source, q=q)
    return render(request, "manage/activity.html", {
        "rows": rows[:per], "has_next": len(rows) > per, "page": page, "source": source, "q": q,
        "show_site": access.site_admin(request.user), "show_sales": access.is_super(request.user),
    })


# -- the command bar ----------------------------------------------------------

@manage_required
def search(request):
    """What the command bar finds beyond page names: posts and pages, users,
    plans, discount codes and drugs -- each for those who may open it."""
    user = request.user
    q = (request.GET.get("q") or "").strip()[:80]
    out = []
    if len(q) < 2:
        return JsonResponse({"results": out})
    if access.has_site_role(user):
        from apps.website.panel.views import search_items

        out += search_items(user, q)
    if access.is_super(user):
        from apps.billing.models import DiscountCode, Plan

        latin = q.translate(_LATIN)
        people = User.objects.filter(
            Q(username__icontains=latin) | Q(email__icontains=latin) | Q(learner_profile__phone__icontains=latin)
            | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        ).distinct()[:5]
        out += [{"type": "کاربر", "label": u.get_full_name() or u.get_username(), "url": _url("console:user", u.pk)} for u in people]
        out += [{"type": "پلن", "label": p.name_fa, "url": _url("console:plan_basics", p.pk)}
                for p in Plan.objects.filter(Q(name_fa__icontains=q) | Q(name_en__icontains=q))[:4]]
        out += [{"type": "کد تخفیف", "label": d.code, "url": _url("console:discounts")}
                for d in DiscountCode.objects.filter(code__icontains=latin)[:3]]
    if access.is_operator(user):
        from apps.drugs.models import Ingredient

        drugs = Ingredient.objects.filter(Q(name__icontains=q) | Q(name_fa__icontains=q))[:5]
        out += [{"type": "دارو", "label": d.name, "url": _url("data_quality_center:workspace", d.slug)} for d in drugs]
    return JsonResponse({"results": [r for r in out if r["url"]]})


# -- old addresses ------------------------------------------------------------

def moved(prefix, base=""):
    """A view sending an old tool address (/ops/..., /panel/...) to its
    place under /manage/, query string kept. `base`: a setting holding the
    admin's own origin, for the site's domains."""

    def view(request, rest=""):
        root = getattr(settings, base).rstrip("/") if base else "/manage"
        target = f"{root}/{prefix}/{rest}"
        if request.META.get("QUERY_STRING"):
            target += "?" + request.META["QUERY_STRING"]
        return HttpResponseRedirect(target)

    return view
