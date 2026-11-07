from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.core.exceptions import PlatformAPIError

from .models import Conversation, Message, PushSubscription
from .serializers import ConversationCreateSerializer, ConversationSerializer, MessageSerializer, MessagePageSerializer, ReadSerializer, SendSerializer, SubscriptionSerializer, SupportSummarySerializer, SubscriptionResponseSerializer
from .services import conversations_for, mark_read, send_message


class SupportView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "sustained"


class ConversationListView(SupportView):
    @extend_schema(responses=ConversationSerializer(many=True))
    def get(self, request):
        return Response(ConversationSerializer(conversations_for(request.user)[:100], many=True).data)

    @extend_schema(request=ConversationCreateSerializer, responses=ConversationSerializer)
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subject = serializer.validated_data.get("subject", "").strip()
        if subject:
            conversation = Conversation.objects.create(user=request.user, kind="topic", subject=subject)
        else:
            conversation, _ = Conversation.objects.get_or_create(user=request.user, kind="general")
        return Response(ConversationSerializer(conversation).data, status=201)


class MessageListView(SupportView):
    @extend_schema(responses=MessagePageSerializer)
    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id, user=request.user)
        try:
            after = max(0, int(request.query_params.get("after", 0)))
            before = max(0, int(request.query_params.get("before", 0)))
        except ValueError:
            after, before = 0, 0
        qs = Message.objects.filter(conversation=conversation)
        if after:
            rows = list(qs.filter(pk__gt=after)[:100])
        else:
            if before:
                qs = qs.filter(pk__lt=before)
            rows = list(reversed(list(qs.order_by("-id")[:100])))
        return Response({"messages": MessageSerializer(rows, many=True).data, "user_read_id": conversation.user_read_id, "staff_read_id": conversation.staff_read_id, "has_older": bool(rows and Message.objects.filter(conversation=conversation, pk__lt=rows[0].pk).exists())})

    @extend_schema(request=SendSerializer, responses=MessageSerializer)
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id, user=request.user)
        serializer = SendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message, created = send_message(conversation, request.user, **serializer.validated_data)
        return Response(MessageSerializer(message).data, status=201 if created else 200)


class ReadView(SupportView):
    @extend_schema(request=ReadSerializer, responses={204: None})
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id, user=request.user)
        serializer = ReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mark_read(conversation, serializer.validated_data["through"])
        return Response(status=204)


class SummaryView(SupportView):
    @extend_schema(responses=SupportSummarySerializer)
    def get(self, request):
        enabled = settings.SUPPORT_PUSH_NOTIFICATIONS_ENABLED
        return Response({"unread": Message.objects.filter(conversation__user=request.user, from_staff=True, id__gt=F("conversation__user_read_id")).count(), "push_enabled": enabled, "web_push_public_key": settings.SUPPORT_WEB_PUSH_PUBLIC_KEY if enabled else "", "web_push_configured": bool(enabled and settings.SUPPORT_WEB_PUSH_PUBLIC_KEY and settings.SUPPORT_WEB_PUSH_PRIVATE_KEY)})


class SubscriptionView(SupportView):
    @extend_schema(request=SubscriptionSerializer, responses=SubscriptionResponseSerializer)
    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["enabled"] and not settings.SUPPORT_PUSH_NOTIFICATIONS_ENABLED:
            raise PlatformAPIError("اعلان‌های پشتیبانی فعلاً غیرفعال هستند.", code="SUPPORT_NOTIFICATIONS_DISABLED", status_code=503)
        # A shared browser/install moving to another account must stop sending
        # that device the previous account's private notifications.
        PushSubscription.objects.filter(device_id=data["device_id"]).exclude(user=request.user).update(enabled=False)
        PushSubscription.objects.update_or_create(user=request.user, device_id=data.pop("device_id"), defaults={**data, "session": request.auth})
        return Response({"enabled": data["enabled"]})
