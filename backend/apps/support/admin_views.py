from functools import wraps

from django.conf import settings
from django.db.models import Count, F, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET

from apps.manage.views import manage_required
from .models import Conversation, Message
from .serializers import MessageSerializer, ReadSerializer, SendSerializer
from .services import can_support, mark_read, send_message


def support_required(view):
    @manage_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not can_support(request.user):
            return HttpResponseForbidden("این بخش فقط برای تیم پشتیبانی قابل دسترسی است.")
        return view(request, *args, **kwargs)
    return wrapper


@support_required
def inbox(request, conversation_id=None):
    qs = Conversation.objects.select_related("user").annotate(unread=Count("messages", filter=Q(messages__from_staff=False, messages__id__gt=F("staff_read_id"))))
    q = request.GET.get("q", "").strip()[:120]
    state = request.GET.get("state", "open")
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(subject__icontains=q))
    if state == "unread":
        qs = qs.filter(unread__gt=0)
    elif state in {"open", "closed"}:
        qs = qs.filter(status=state)
    total = qs.count()
    conversations = list(qs.order_by("-unread", "-updated_at")[:100])
    current = get_object_or_404(Conversation.objects.select_related("user"), pk=conversation_id) if conversation_id else None
    messages = list(reversed(list(current.messages.order_by("-pk")[:100]))) if current else []
    return render(request, "support/inbox.html", {"conversations": conversations, "total": total, "conversation": current, "chat_messages": messages, "q": q, "state": state, "web_push_ready": bool(settings.SUPPORT_WEB_PUSH_PUBLIC_KEY and settings.SUPPORT_WEB_PUSH_PRIVATE_KEY)})


@require_GET
@support_required
def message_list(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    try:
        after = max(0, int(request.GET.get("after", 0)))
        before = max(0, int(request.GET.get("before", 0)))
    except ValueError:
        return JsonResponse({"error": "شناسهٔ پیام نامعتبر است."}, status=400)
    qs = conversation.messages.all()
    if before:
        rows = list(reversed(list(qs.filter(pk__lt=before).order_by("-id")[:100])))
    else:
        rows = list(qs.filter(pk__gt=after)[:100])
    return JsonResponse({"messages": MessageSerializer(rows, many=True).data, "has_older": bool(rows and qs.filter(pk__lt=rows[0].pk).exists()), "user_read_id": conversation.user_read_id})


@require_POST
@support_required
def reply(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    serializer = SendSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({"error": "متن پیام و شناسهٔ ارسال معتبر لازم است."}, status=400)
    message, created = send_message(conversation, request.user, **serializer.validated_data, staff=True)
    return JsonResponse(MessageSerializer(message).data, status=201 if created else 200)


@require_POST
@support_required
def read(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    serializer = ReadSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({"error": "شناسهٔ پیام معتبر نیست."}, status=400)
    mark_read(conversation, serializer.validated_data["through"], staff=True)
    return JsonResponse({"ok": True})


@require_POST
@support_required
def close(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if request.POST.get("subject", "").strip():
        conversation.subject = request.POST["subject"].strip()[:120]
    conversation.status = "closed" if request.POST.get("status") == "closed" else "open"
    conversation.save(update_fields=["status", "subject"])
    return redirect("support_admin:conversation", conversation_id=conversation.pk)
