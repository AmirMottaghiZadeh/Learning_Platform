"""Internal, staff-only tool for filling in the ingredient section summaries.

Every save writes an append-only `SectionEdit`. Raw label text is read-only.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.drugs.models import CLINICAL_FIELD_KEYS, Ingredient, IngredientProfileSection

from .forms import SectionEditForm
from .models import SectionEdit

PAGE_SIZE = 25


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
        "page": page, "search": search, "missing": missing,
    })


@staff_member_required
def ingredient_detail(request, slug):
    ingredient = get_object_or_404(
        Ingredient.objects.prefetch_related("sections"), slug=slug
    )
    by_field = {s.field: s for s in ingredient.sections.all()}
    sections = [by_field[f] for f in CLINICAL_FIELD_KEYS if f in by_field]
    return render(request, "data_quality_center/detail.html", {
        "ingredient": ingredient, "sections": sections,
    })


@staff_member_required
def section_edit(request, slug, field):
    ingredient = get_object_or_404(Ingredient, slug=slug)
    section = get_object_or_404(IngredientProfileSection, ingredient=ingredient, field=field)

    if request.method != "POST":
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

    SectionEdit.objects.create(
        section=section,
        editor=request.user,
        editor_username=request.user.get_username(),
        ingredient_name=ingredient.name,
        field=field,
        before_fa=section.summary_fa,
        after_fa=new_fa,
        before_en=section.summary_en,
        after_en=new_en,
        reason=form.cleaned_data["reason"],
    )
    section.summary_fa = new_fa
    section.summary_en = new_en
    section.save(update_fields=["summary_fa", "summary_en", "updated_at"])
    messages.success(request, f"Saved {ingredient.name} · {section.get_field_display()}.")
    return redirect("data_quality_center:ingredient_detail", slug=slug)


@staff_member_required
def edit_history(request):
    page = Paginator(
        SectionEdit.objects.select_related("editor"), PAGE_SIZE
    ).get_page(request.GET.get("page"))
    return render(request, "data_quality_center/history.html", {"page": page})
