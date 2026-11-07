"""The admin's «اعلانات اپ» (apps.manage): the announcements beside the one
being edited, with a live preview of the app's card and what learners did
with it. For superusers."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.billing import services as billing
from apps.billing.console.views import superuser_required

from . import services
from .forms import AnnouncementForm
from .models import AppAnnouncement

STATES = [("", "همه")] + list(AppAnnouncement.STATE_LABELS.items())


def _page(request, item, form):
    now = timezone.now()
    state = request.GET.get("state", "")
    rows = list(services.with_figures(AppAnnouncement.objects.all()))
    counts = {key: sum(1 for r in rows if r.state_at(now) == key) for key in AppAnnouncement.STATE_LABELS}
    shown = [r for r in rows if not state or r.state_at(now) == state]
    figures = next((r for r in rows if item and r.pk == item.pk), None)
    return render(request, "announcements/manage.html", {
        "item": item, "form": form, "rows": shown, "state": state, "now": now, "figures": figures,
        "states": [(key, label, counts.get(key, len(rows))) for key, label in STATES],
        "screens": AppAnnouncement.SCREEN_CHOICES,
    })


@superuser_required
def announcements(request):
    """The list with a blank editor for a new one."""
    return _page(request, None, AnnouncementForm(initial={"dismissible": True}))


@superuser_required
def announcement(request, pk=None):
    item = get_object_or_404(AppAnnouncement, pk=pk) if pk else None
    if request.method != "POST":
        return _page(request, item, AnnouncementForm(instance=item))
    form = AnnouncementForm(request.POST, instance=item)
    if not form.is_valid():
        messages.error(request, "ذخیره نشد؛ خطاهای فرم را ببینید.")
        return _page(request, item, form)
    action = request.POST.get("action", "save")
    obj = form.save(commit=False)
    if obj.created_by_id is None:
        obj.created_by = request.user
    if action == "publish":
        obj.is_published = True
    elif action == "test":
        obj.test_user = request.user
    obj.save()
    if action == "publish":
        billing.record(request, "announcement_publish", f"انتشار اعلان اپ «{obj.title}»", details={"announcement": obj.pk})
        messages.success(request, "منتشر شد." if obj.state == AppAnnouncement.STATE_ACTIVE else "ذخیره شد و سر وقتش نمایش داده می‌شود.")
    elif action == "test":
        messages.success(request, "حالا در اپ خودتان، در خانه، دیده می‌شود؛ برای بقیه نه، تا منتشرش کنید.")
    else:
        messages.success(request, "ذخیره شد.")
    return redirect("app_admin:announcement", pk=obj.pk)


@superuser_required
@require_POST
def announcement_action(request, pk):
    item = get_object_or_404(AppAnnouncement, pk=pk)
    action = request.POST.get("action")
    if action == "end":
        item.ends_at = timezone.now()
        item.save(update_fields=["ends_at", "updated_at"])
        billing.record(request, "announcement_end", f"پایان اعلان اپ «{item.title}»", details={"announcement": item.pk})
        messages.success(request, "تمام شد؛ دیگر در اپ دیده نمی‌شود.")
    elif action == "unpublish":
        item.is_published = False
        item.save(update_fields=["is_published", "updated_at"])
        billing.record(request, "announcement_unpublish", f"برگرداندن اعلان اپ «{item.title}» به پیش‌نویس", details={"announcement": item.pk})
        messages.success(request, "به پیش‌نویس برگشت.")
    elif action == "untest":
        item.test_user = None
        item.save(update_fields=["test_user", "updated_at"])
        messages.success(request, "از اپ شما برداشته شد.")
    elif action == "delete":
        billing.record(request, "announcement_delete", f"حذف اعلان اپ «{item.title}»", details={"announcement": item.pk})
        item.delete()
        messages.success(request, "حذف شد.")
        return redirect("app_admin:announcements")
    return redirect(reverse("app_admin:announcement", args=[item.pk]))
