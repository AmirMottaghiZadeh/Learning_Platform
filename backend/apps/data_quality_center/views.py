"""The Data Quality Center console: staff operators fill in and correct the
ingredient section summaries next to the raw label text; a superuser
reviews every change before it reaches the live data. Server-rendered,
Persian, right to left; the workflow itself lives in services.py.
"""

from functools import wraps

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.manage.views import login_url as manage_login_url
from apps.manage.views import logout_view as manage_logout
from apps.manage.views import to_login
from apps.drugs.models import CLINICAL_FIELD_KEYS, Ingredient, IngredientProfileSection

from . import services
from .checks import run_checks, warning_count, word_diff
from .labels import FIELD_FA, section_state
from .models import ReviewEvent, SectionEdit, SectionEditRequest
from .services import WorkflowError

PAGE_SIZE = 25


# -- access -----------------------------------------------------------------

def operator_required(view):
    """Signed-in, active staff only; anyone else goes to the console's own
    sign-in page."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.is_active and user.is_staff):
            return redirect(manage_login_url(request.get_full_path()))
        return view(request, *args, **kwargs)

    return wrapper


def superuser_required(view):
    @operator_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "این بخش فقط برای سوپریوزر است.")
            return redirect("data_quality_center:queue")
        return view(request, *args, **kwargs)

    return wrapper


# Signing in and out is the admin's (apps.manage); these old addresses send there.
login_view = to_login


@require_POST
def logout_view(request):
    return manage_logout(request)


# -- shared page data ---------------------------------------------------------

def _shell(request, active):
    """What every console page's top bar and sidebar show."""
    user = request.user
    mine = SectionEditRequest.objects.filter(requested_by=user)
    today = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    counts = mine.aggregate(
        drafts=Count("pk", filter=Q(status=SectionEditRequest.STATUS_DRAFT)),
        pending=Count("pk", filter=Q(status=SectionEditRequest.STATUS_PENDING)),
        changes=Count("pk", filter=Q(status=SectionEditRequest.STATUS_CHANGES_REQUESTED)),
    )
    return {
        "active": active,
        "nav": {
            "my_open": counts["drafts"] + counts["pending"] + counts["changes"],
            "changes": counts["changes"],
            "review": (
                SectionEditRequest.objects.filter(status=SectionEditRequest.STATUS_PENDING).count()
                if user.is_superuser else 0
            ),
            "ingredients": Ingredient.objects.count(),
        },
        "today": {
            "submitted": ReviewEvent.objects.filter(
                actor=user, action__in=[ReviewEvent.SUBMITTED, ReviewEvent.RESUBMITTED], created_at__gte=today
            ).count(),
            "approved": ReviewEvent.objects.filter(
                request__requested_by=user, action=ReviewEvent.APPROVED, created_at__gte=today
            ).count(),
        },
    }


def _render(request, template, active, context):
    return render(request, f"data_quality_center/{template}", {**_shell(request, active), **context})


def _diffs(before_fa, after_fa, before_en, after_en):
    fa_html, fa_add, fa_del = word_diff(before_fa, after_fa)
    en_html, en_add, en_del = word_diff(before_en, after_en)
    return {
        "fa": fa_html, "en": en_html,
        "added": fa_add + en_add, "removed": fa_del + en_del,
        "fa_added": fa_add, "fa_removed": fa_del, "en_added": en_add, "en_removed": en_del,
    }


# -- edit queue -----------------------------------------------------------------

QUEUE_FILTERS = {
    "": "همه",
    "missing": "بدون خلاصه",
    "pending": "در انتظار تأیید",
    "changes": "نیاز به اصلاح",
    "mine": "پیش‌نویس‌های من",
}


@operator_required
def queue(request):
    search = request.GET.get("q", "").strip()
    show = request.GET.get("show", "")
    if show not in QUEUE_FILTERS:
        show = ""

    with_raw = Q(sections__raw_text__gt="")
    qs = Ingredient.objects.annotate(
        total=Count("sections", filter=with_raw, distinct=True),
        filled=Count(
            "sections",
            filter=with_raw & ~Q(sections__summary_fa="") & ~Q(sections__summary_en=""),
            distinct=True,
        ),
        pending=Count(
            "sections__edit_requests",
            filter=Q(sections__edit_requests__status=SectionEditRequest.STATUS_PENDING),
            distinct=True,
        ),
        changes=Count(
            "sections__edit_requests",
            filter=Q(sections__edit_requests__status=SectionEditRequest.STATUS_CHANGES_REQUESTED),
            distinct=True,
        ),
    ).order_by("name")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(rxcui=search))
    if show == "missing":
        qs = qs.filter(with_raw & (Q(sections__summary_fa="") | Q(sections__summary_en=""))).distinct()
    elif show == "pending":
        qs = qs.filter(sections__edit_requests__status=SectionEditRequest.STATUS_PENDING).distinct()
    elif show == "changes":
        qs = qs.filter(
            sections__edit_requests__status=SectionEditRequest.STATUS_CHANGES_REQUESTED,
            sections__edit_requests__requested_by=request.user,
        ).distinct()
    elif show == "mine":
        qs = qs.filter(
            sections__edit_requests__status=SectionEditRequest.STATUS_DRAFT,
            sections__edit_requests__requested_by=request.user,
        ).distinct()

    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return _render(request, "queue.html", "queue", {
        "page": page, "search": search, "show": show, "filters": QUEUE_FILTERS,
    })


# -- workspace ----------------------------------------------------------------

def _neighbours(ingredient):
    before = Ingredient.objects.filter(name__lt=ingredient.name).order_by("-name").values_list("slug", flat=True).first()
    after = Ingredient.objects.filter(name__gt=ingredient.name).order_by("name").values_list("slug", flat=True).first()
    return before, after


@operator_required
def workspace(request, slug):
    ingredient = get_object_or_404(Ingredient, slug=slug)
    by_field = {s.field: s for s in IngredientProfileSection.objects.filter(ingredient=ingredient)}
    sections = [by_field[f] for f in CLINICAL_FIELD_KEYS if f in by_field]
    if not sections:
        return _render(request, "workspace.html", "queue", {"ingredient": ingredient, "sections": []})

    section_ids = [s.pk for s in sections]
    open_by_section = {
        r.section_id: r
        for r in SectionEditRequest.objects.filter(
            section_id__in=section_ids, status__in=SectionEditRequest.OPEN_STATUSES
        )
    }
    my_drafts = set(
        SectionEditRequest.objects.filter(
            section_id__in=section_ids, requested_by=request.user, status=SectionEditRequest.STATUS_DRAFT
        ).values_list("section_id", flat=True)
    )
    applied = set(SectionEdit.objects.filter(section_id__in=section_ids).values_list("section_id", flat=True))

    field = request.GET.get("field")
    selected = by_field.get(field)
    if selected is None:
        # first section that still needs work, else the first one
        selected = next(
            (s for s in sections if s.raw_text and (not s.summary_fa or not s.summary_en)), sections[0]
        )

    rows = [
        {
            "section": s,
            "label": FIELD_FA.get(s.field, s.get_field_display()),
            "state": section_state(s, open_by_section.get(s.pk), s.pk in my_drafts, s.pk in applied, request.user),
            "selected": s.pk == selected.pk,
        }
        for s in sections
    ]
    done = sum(1 for r in rows if r["state"]["key"] in ("approved", "unreviewed"))
    waiting = sum(1 for r in rows if r["state"]["key"] == "pending")

    held = open_by_section.get(selected.pk)
    mine = services.editable_request(selected, request.user)
    if held and held.requested_by_id != request.user.id:
        mode, current = "locked", held
    elif held and held.is_pending:
        mode, current = "pending", held
    else:
        mode, current = "edit", mine

    if mode == "edit":
        draft_fa = current.after_fa if current else selected.summary_fa
        draft_en = current.after_en if current else selected.summary_en
        base_fa = current.before_fa if current else selected.summary_fa
        base_en = current.before_en if current else selected.summary_en
        checks = run_checks(selected.raw_text, base_fa, draft_fa, base_en, draft_en)
    else:
        draft_fa, draft_en = current.after_fa, current.after_en
        base_fa, base_en = current.before_fa, current.before_en
        checks = current.checks

    last_edit = SectionEdit.objects.filter(section=selected).first()
    previous_slug, next_slug = _neighbours(ingredient)

    return _render(request, "workspace.html", "queue", {
        "ingredient": ingredient,
        "sections": rows,
        "done": done,
        "waiting": waiting,
        "total": len(rows),
        "section": selected,
        "section_label": FIELD_FA.get(selected.field, selected.get_field_display()),
        "mode": mode,
        "current": current,
        "draft_fa": draft_fa,
        "draft_en": draft_en,
        "checks": checks,
        "warnings": warning_count(checks),
        "diff": _diffs(base_fa, draft_fa, base_en, draft_en),
        "events": current.events.all()[:20] if current else [],
        "last_edit": last_edit,
        "previous_slug": previous_slug,
        "next_slug": next_slug,
        "min_reason": services.min_reason_length(),
    })


def _section_or_404(slug, field):
    return get_object_or_404(
        IngredientProfileSection.objects.select_related("ingredient"), ingredient__slug=slug, field=field
    )


def _workspace_url(slug, field):
    return f"{reverse('data_quality_center:workspace', args=[slug])}?field={field}"


@require_POST
@operator_required
def save_draft(request, slug, field):
    """Autosave: stores the editor's content as the operator's draft and
    answers with the live checks and diff."""
    section = _section_or_404(slug, field)
    try:
        req = services.save_draft(
            section,
            request.user,
            summary_fa=request.POST.get("summary_fa", ""),
            summary_en=request.POST.get("summary_en", ""),
            reason=request.POST.get("reason", ""),
        )
    except WorkflowError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=409)
    checks = run_checks(section.raw_text, req.before_fa, req.after_fa, req.before_en, req.after_en)
    return JsonResponse({
        "ok": True,
        "request_id": req.pk,
        "status": req.status,
        "saved_at": timezone.localtime(req.updated_at).strftime("%H:%M"),
        "checks": checks,
        "warnings": warning_count(checks),
        "diff": _diffs(req.before_fa, req.after_fa, req.before_en, req.after_en),
    })


@require_POST
@operator_required
def submit(request, slug, field):
    section = _section_or_404(slug, field)
    try:
        req = services.save_draft(
            section,
            request.user,
            summary_fa=request.POST.get("summary_fa", ""),
            summary_en=request.POST.get("summary_en", ""),
            reason=request.POST.get("reason", ""),
        )
        services.submit(req, request.user, http_request=request)
    except WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"درخواست #{req.pk} برای تأیید نهایی سوپریوزر فرستاده شد.")
    return redirect(_workspace_url(slug, field))


@require_POST
@operator_required
def withdraw(request, slug, field):
    section = _section_or_404(slug, field)
    req = get_object_or_404(
        SectionEditRequest, section=section, requested_by=request.user, status=SectionEditRequest.STATUS_PENDING
    )
    try:
        services.withdraw(req, request.user, http_request=request)
    except WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.info(request, "درخواست پس گرفته شد و دوباره قابل ویرایش است.")
    return redirect(_workspace_url(slug, field))


@require_POST
@operator_required
def discard(request, slug, field):
    section = _section_or_404(slug, field)
    req = services.editable_request(section, request.user)
    if req is None:
        return redirect(_workspace_url(slug, field))
    try:
        services.discard(req, request.user, http_request=request)
    except WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.info(request, "تغییرات کنار گذاشته شد.")
    return redirect(_workspace_url(slug, field))


# -- my requests ----------------------------------------------------------------

MINE_TABS = {
    "open": ("باز", SectionEditRequest.EDITABLE_STATUSES + (SectionEditRequest.STATUS_PENDING,)),
    "approved": ("تأییدشده", (SectionEditRequest.STATUS_APPROVED,)),
    "closed": ("ردشده یا کنارگذاشته", (SectionEditRequest.STATUS_REJECTED, SectionEditRequest.STATUS_DISCARDED)),
}


@operator_required
def my_requests(request):
    tab = request.GET.get("tab", "open")
    if tab not in MINE_TABS:
        tab = "open"
    qs = (
        SectionEditRequest.objects.filter(requested_by=request.user, status__in=MINE_TABS[tab][1])
        .select_related("section__ingredient")
        .order_by("-updated_at")
    )
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    for req in page:
        req.field_label = FIELD_FA.get(req.field, req.get_field_display())
    return _render(request, "mine.html", "mine", {
        "page": page, "tab": tab, "tabs": {k: v[0] for k, v in MINE_TABS.items()},
    })


# -- review desk ----------------------------------------------------------------

@superuser_required
def review_desk(request):
    pending = list(
        SectionEditRequest.objects.filter(status=SectionEditRequest.STATUS_PENDING)
        .select_related("section__ingredient")
        .order_by("submitted_at", "pk")
    )
    for req in pending:
        req.field_label = FIELD_FA.get(req.field, req.get_field_display())
        _, req.added, req.removed = word_diff(
            f"{req.before_fa} {req.before_en}", f"{req.after_fa} {req.after_en}"
        )
        req.warnings = warning_count(req.checks)

    selected = None
    wanted = request.GET.get("id")
    if wanted and wanted.isdigit():
        selected = next((r for r in pending if r.pk == int(wanted)), None)
    if selected is None and pending:
        selected = pending[0]

    context = {"pending": pending, "selected": selected}
    if selected:
        section = selected.section
        context.update({
            "diff": _diffs(selected.before_fa, selected.after_fa, selected.before_en, selected.after_en),
            "events": selected.events.all(),
            "drifted": section.summary_fa != selected.before_fa or section.summary_en != selected.before_en,
            "workspace_url": _workspace_url(section.ingredient.slug, section.field),
        })
    return _render(request, "review.html", "review", context)


@require_POST
@superuser_required
def review_action(request, pk):
    req = get_object_or_404(SectionEditRequest, pk=pk)
    action = request.POST.get("action")
    note = request.POST.get("note", "").strip()
    label = f"#{req.pk} · {req.ingredient_name}"
    try:
        if action == "approve":
            services.approve(req, request.user, note, http_request=request)
            messages.success(request, f"{label} تأیید و در دیتابیس اعمال شد.")
        elif action == "changes":
            services.request_changes(req, request.user, note, http_request=request)
            messages.info(request, f"{label} برای اصلاح به اپراتور برگشت.")
        elif action == "reject":
            services.reject(req, request.user, note, http_request=request)
            messages.info(request, f"{label} رد شد.")
        else:
            messages.error(request, "اقدام نامعتبر.")
    except WorkflowError as exc:
        messages.error(request, str(exc))
        return redirect(f"{reverse('data_quality_center:review')}?id={req.pk}")
    return redirect("data_quality_center:review")


# -- history & audit ----------------------------------------------------------

@operator_required
def history(request):
    tab = request.GET.get("tab", "events")
    search = request.GET.get("q", "").strip()
    action = request.GET.get("action", "")
    section_id = request.GET.get("section", "")

    if tab == "edits":
        qs = SectionEdit.objects.select_related("section__ingredient").prefetch_related("revert_requests")
        if search:
            qs = qs.filter(Q(ingredient_name__icontains=search) | Q(editor_username__icontains=search))
        if section_id.isdigit():
            qs = qs.filter(section_id=int(section_id))
        page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
        for edit in page:
            edit.field_label = FIELD_FA.get(edit.field, edit.get_field_display())
            edit.diff = _diffs(edit.before_fa, edit.after_fa, edit.before_en, edit.after_en)
            edit.reverted = any(r.status == SectionEditRequest.STATUS_APPROVED for r in edit.revert_requests.all())
            edit.revert_open = any(r.status in SectionEditRequest.OPEN_STATUSES for r in edit.revert_requests.all())
    else:
        tab = "events"
        qs = ReviewEvent.objects.select_related("request__section__ingredient")
        if search:
            qs = qs.filter(Q(request__ingredient_name__icontains=search) | Q(actor_username__icontains=search))
        if action in dict(ReviewEvent.ACTION_CHOICES):
            qs = qs.filter(action=action)
        if section_id.isdigit():
            qs = qs.filter(request__section_id=int(section_id))
        page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
        for event in page:
            event.field_label = FIELD_FA.get(event.request.field, event.request.get_field_display())

    return _render(request, "history.html", "history", {
        "tab": tab, "page": page, "search": search, "action": action, "section_id": section_id,
        "actions": ReviewEvent.ACTION_CHOICES,
        "min_reason": services.min_reason_length(),
    })


@require_POST
@superuser_required
def revert(request, pk):
    edit = get_object_or_404(SectionEdit, pk=pk)
    try:
        req = services.start_revert(edit, request.user, request.POST.get("reason", ""), http_request=request)
    except WorkflowError as exc:
        messages.error(request, str(exc))
        return redirect(f"{reverse('data_quality_center:history')}?tab=edits")
    messages.success(request, f"درخواست بازگردانی #{req.pk} ساخته شد؛ آن را در میز بررسی تأیید کنید.")
    return redirect(f"{reverse('data_quality_center:review')}?id={req.pk}")
