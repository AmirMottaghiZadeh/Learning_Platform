"""The media library and its picker."""

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import Media, Post, SiteSettings
from ..permissions import can, panel_required
from . import forms
from .ui import log, paginate, render_panel


def _item(m):
    return {"id": m.pk, "url": m.url, "title": m.title or m.filename, "alt": m.alt, "image": m.is_image, "size": m.size, "type": m.content_type}


@panel_required("media.upload")
def media_list(request):
    qs = Media.objects.defer("data")
    q = (request.GET.get("q") or "").strip()
    kind = request.GET.get("type", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(filename__icontains=q) | Q(alt__icontains=q))
    if kind == "image":
        qs = qs.filter(content_type__startswith="image/")
    elif kind == "pdf":
        qs = qs.filter(content_type="application/pdf")
    page = paginate(request, qs, 24)
    used = set(Post.objects.filter(cover__in=[m.pk for m in page.object_list]).values_list("cover_id", flat=True))
    return render_panel(request, "panel/media.html", {"page": page, "q": q, "type": kind, "used": used, "total": Media.objects.count()}, active="media")


@require_POST
@panel_required("media.upload")
def media_upload(request):
    created, errors = [], []
    for upload in request.FILES.getlist("files"):
        try:
            created.append(Media.from_upload(upload, user=request.user))
        except ValueError as exc:
            errors.append(f"{upload.name}: {exc}")
    for m in created:
        log(request, "upload", m)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"items": [_item(m) for m in created], "errors": errors}, status=200 if created or not errors else 400)
    for e in errors:
        messages.error(request, e)
    if created:
        messages.success(request, f"{len(created)} فایل بارگذاری شد.")
    return redirect("panel:media")


@panel_required("media.upload")
def media_edit(request, pk):
    item = get_object_or_404(Media.objects.defer("data"), pk=pk)
    form = forms.MediaMetaForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        log(request, "update", item)
        messages.success(request, "ذخیره شد.")
        return redirect("panel:media")
    return render_panel(request, "panel/media_edit.html", {
        "form": form, "item": item, "used_in": Post.objects.filter(cover=item)[:10],
        "is_default_og": SiteSettings.get().default_og_image_id == item.pk,
    }, active="media")


@require_POST
@panel_required("media.manage")
def media_delete(request, pk):
    item = get_object_or_404(Media.objects.defer("data"), pk=pk)
    log(request, "delete", item)
    item.delete()
    messages.success(request, "فایل حذف شد.")
    return redirect("panel:media")


@panel_required("media.upload")
def media_picker(request):
    qs = Media.objects.defer("data")
    if request.GET.get("type") == "image":
        qs = qs.filter(content_type__startswith="image/")
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(filename__icontains=q))
    page = paginate(request, qs, 18)
    return JsonResponse({"items": [_item(m) for m in page.object_list], "has_next": page.has_next(), "page": page.number})
