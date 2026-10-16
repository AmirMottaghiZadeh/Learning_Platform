"""Comments, contact messages and newsletter subscribers."""

import csv

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import Comment, ContactMessage, Subscriber
from ..permissions import panel_required
from .ui import jalali_format, log, paginate, render_panel


@panel_required("comment.moderate")
def comments(request):
    status = request.GET.get("status", "pending")
    qs = Comment.objects.select_related("post", "parent")
    counts = dict(Comment.objects.values_list("status").annotate(n=Count("id")))
    if status in dict(Comment.STATUS_CHOICES):
        qs = qs.filter(status=status)
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(body__icontains=q) | Q(email__icontains=q))
    tabs = [(k, label, counts.get(k, 0)) for k, label in Comment.STATUS_CHOICES]
    return render_panel(request, "panel/comments.html", {
        "page": paginate(request, qs.order_by("-created_at"), 20), "status": status, "tabs": tabs, "q": q,
    }, active="comments")


@require_POST
@panel_required("comment.moderate")
def comment_action(request):
    action = request.POST.get("action")
    one = request.GET.get("one", "")
    ids = [one] if one.isdigit() else [i for i in request.POST.getlist("ids") if i.isdigit()]
    rows = Comment.objects.filter(pk__in=ids)
    n = rows.count()
    if action == "approve":
        rows.update(status=Comment.APPROVED)
    elif action == "spam":
        rows.update(status=Comment.SPAM)
    elif action == "trash":
        rows.update(status=Comment.TRASH)
    elif action == "pending":
        rows.update(status=Comment.PENDING)
    elif action == "delete":
        rows.delete()
    elif action == "reply":
        parent = rows.first()
        text = (request.POST.get("reply") or "").strip()[:2000]
        if parent and text:
            top = parent.parent or parent
            Comment.objects.create(post=parent.post, parent=top, name=request.user.get_full_name() or "تیم سایت", body=text,
                                   status=Comment.APPROVED, is_staff_reply=True)
            if parent.status != Comment.APPROVED:
                parent.status = Comment.APPROVED
                parent.save(update_fields=["status"])
            messages.success(request, "پاسخ شما ثبت شد.")
            log(request, "comment_reply", parent)
            return redirect(request.META.get("HTTP_REFERER") or reverse("panel:comments"))
    else:
        messages.error(request, "کاری انتخاب نشده است.")
        return redirect(reverse("panel:comments"))
    log(request, f"comment_{action}", detail=f"{n} نظر")
    messages.success(request, f"{n} نظر به‌روزرسانی شد.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("panel:comments"))


@panel_required("contact.view")
def contact(request):
    status = request.GET.get("status", "")
    qs = ContactMessage.objects.all()
    counts = dict(ContactMessage.objects.values_list("status").annotate(n=Count("id")))
    if status in dict(ContactMessage.STATUS_CHOICES):
        qs = qs.filter(status=status)
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(message__icontains=q) | Q(email__icontains=q) | Q(subject__icontains=q))
    tabs = [("", "همه", sum(counts.values()))] + [(k, label, counts.get(k, 0)) for k, label in ContactMessage.STATUS_CHOICES]
    return render_panel(request, "panel/contact.html", {"page": paginate(request, qs, 20), "status": status, "tabs": tabs, "q": q}, active="contact")


@require_POST
@panel_required("contact.view")
def contact_action(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    action = request.POST.get("action")
    if action in dict(ContactMessage.STATUS_CHOICES):
        msg.status = action
        msg.save(update_fields=["status"])
    elif action == "delete":
        log(request, "delete", msg)
        msg.delete()
        messages.success(request, "پیام حذف شد.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("panel:contact"))


@panel_required("subscriber.view")
def subscribers(request):
    qs = Subscriber.objects.all()
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(email__icontains=q)
    return render_panel(request, "panel/subscribers.html", {
        "page": paginate(request, qs, 30), "q": q, "total": Subscriber.objects.count(), "active": Subscriber.objects.filter(is_active=True).count(),
    }, active="subscribers")


@panel_required("subscriber.view")
def subscribers_export(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="subscribers.csv"'
    response.write("﻿")
    writer = csv.writer(response)
    writer.writerow(["email", "active", "source", "joined"])
    for s in Subscriber.objects.all():
        writer.writerow([s.email, int(s.is_active), s.source, s.created_at.date().isoformat()])
    log(request, "export_subscribers")
    return response


@require_POST
@panel_required("subscriber.view")
def subscriber_action(request, pk):
    sub = get_object_or_404(Subscriber, pk=pk)
    if request.POST.get("action") == "delete":
        log(request, "delete", sub)
        sub.delete()
    else:
        sub.is_active = not sub.is_active
        sub.save(update_fields=["is_active"])
    return redirect(request.META.get("HTTP_REFERER") or reverse("panel:subscribers"))
