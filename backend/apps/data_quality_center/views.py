"""Internal, staff-only tool for filling in the ingredient section summaries.

An edit is a two-step process: any staff operator can submit one (creates a
pending `SectionEditRequest`), but it only reaches the live
`IngredientProfileSection` -- and only then writes the permanent,
append-only `SectionEdit` ledger row -- once a superuser approves it.
Raw label text is read-only throughout.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.drugs.models import CLINICAL_FIELD_KEYS, Ingredient, IngredientProfileSection

from .forms import ReviewForm, SectionEditForm
from .models import SectionEditRequest

PAGE_SIZE = 25


def _require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only a superuser can review edit requests.")


def _pending_count():
    return SectionEditRequest.objects.filter(status=SectionEditRequest.STATUS_PENDING).count()


@staff_member_required
def ingredient_list(request):
    search = request.GET.get("q", "").strip()
    missing = request.GET.get("missing", "")  # "", "fa", "en", "any"

    qs = Ingredient.objects.order_by("name")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(rxcui=search))
    if missing in {"fa", "en", "any"}:
        cond = Q(sections__raw_text__gt="")
        if missing == "fa":
            cond &= Q(sections__summary_fa="")
        elif missing == "en":
            cond &= Q(sections__summary_en="")
        else:
            cond &= (Q(sections__summary_fa="") | Q(sections__summary_en=""))
        qs = qs.filter(cond).distinct()

    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "data_quality_center/list.html", {
        "page": page, "search": search, "missing": missing, "pending_count": _pending_count(),
    })


@staff_member_required
def ingredient_detail(request, slug):
    ingredient = get_object_or_404(
        Ingredient.objects.prefetch_related("sections"), slug=slug
    )
    by_field = {s.field: s for s in ingredient.sections.all()}
    sections = [by_field[f] for f in CLINICAL_FIELD_KEYS if f in by_field]
    pending_by_field = {
        r.field: r
        for r in SectionEditRequest.objects.filter(
            section__ingredient=ingredient, status=SectionEditRequest.STATUS_PENDING
        )
    }
    return render(request, "data_quality_center/detail.html", {
        "ingredient": ingredient,
        "sections": sections,
        "pending_by_field": pending_by_field,
        "pending_count": _pending_count(),
    })


@staff_member_required
def section_edit(request, slug, field):
    ingredient = get_object_or_404(Ingredient, slug=slug)
    section = get_object_or_404(IngredientProfileSection, ingredient=ingredient, field=field)

    if request.method != "POST":
        return redirect("data_quality_center:ingredient_detail", slug=slug)

    if SectionEditRequest.objects.filter(
        section=section, status=SectionEditRequest.STATUS_PENDING
    ).exists():
        messages.error(
            request,
            f"A request for {ingredient.name} · {section.get_field_display()} is already "
            "awaiting superuser review.",
        )
        return redirect("data_quality_center:ingredient_detail", slug=slug)

    form = SectionEditForm(request.POST)
    if not form.is_valid():
        messages.error(request, "; ".join(sum(form.errors.values(), [])))
        return redirect("data_quality_center:ingredient_detail", slug=slug)

    new_fa = form.cleaned_data["summary_fa"].strip()
    new_en = form.cleaned_data["summary_en"].strip()
    if new_fa == section.summary_fa and new_en == section.summary_en:
        messages.info(request, "No change.")
        return redirect("data_quality_center:ingredient_detail", slug=slug)

    SectionEditRequest.objects.create(
        section=section,
        requested_by=request.user,
        requested_by_username=request.user.get_username(),
        ingredient_name=ingredient.name,
        field=field,
        before_fa=section.summary_fa,
        after_fa=new_fa,
        before_en=section.summary_en,
        after_en=new_en,
        reason=form.cleaned_data["reason"],
    )
    messages.success(
        request,
        f"Submitted {ingredient.name} · {section.get_field_display()} for superuser approval.",
    )
    return redirect("data_quality_center:ingredient_detail", slug=slug)


@staff_member_required
def pending_requests(request):
    page = Paginator(
        SectionEditRequest.objects.filter(status=SectionEditRequest.STATUS_PENDING)
        .select_related("requested_by"),
        PAGE_SIZE,
    ).get_page(request.GET.get("page"))
    return render(request, "data_quality_center/requests.html", {
        "page": page, "pending_count": _pending_count(), "review_form": ReviewForm(),
    })


@staff_member_required
def review_request(request, request_id):
    _require_superuser(request)
    edit_request = get_object_or_404(
        SectionEditRequest, pk=request_id, status=SectionEditRequest.STATUS_PENDING
    )
    if request.method != "POST":
        return redirect("data_quality_center:pending_requests")

    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "; ".join(sum(form.errors.values(), [])))
        return redirect("data_quality_center:pending_requests")

    action = form.cleaned_data["action"]
    note = form.cleaned_data["note"]
    try:
        if action == "approve":
            edit_request.approve(request.user, note=note)
            messages.success(
                request,
                f"Approved and applied {edit_request.ingredient_name} · "
                f"{edit_request.get_field_display()}.",
            )
        else:
            edit_request.reject(request.user, note=note)
            messages.info(
                request,
                f"Rejected {edit_request.ingredient_name} · {edit_request.get_field_display()}.",
            )
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("data_quality_center:pending_requests")


@staff_member_required
def edit_history(request):
    page = Paginator(
        SectionEditRequest.objects.select_related("requested_by", "reviewed_by"), PAGE_SIZE
    ).get_page(request.GET.get("page"))
    return render(request, "data_quality_center/history.html", {
        "page": page, "pending_count": _pending_count(),
    })
