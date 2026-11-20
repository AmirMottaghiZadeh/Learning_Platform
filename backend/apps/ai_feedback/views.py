from django.db import DatabaseError
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.ai_lab.views import require_lab
from apps.core.exceptions import PlatformAPIError
from . import services


class VoteSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[1, -1])


class FeedbackResponseSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[1,-1],allow_null=True)


class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_feedback(self, request, job_id, value=None):
        require_lab(request.user)
        try:
            answer = services.owned_answer(job_id, request.user)
            vote = services.rating(answer) if value is None else services.rate(answer, value)
        except DatabaseError:
            raise PlatformAPIError("ثبت بازخورد ممکن نشد؛ دوباره تلاش کنید.", code="FEEDBACK_UNAVAILABLE", status_code=503) from None
        response = Response({"value": vote})
        response["Cache-Control"] = "private, no-store"
        return response

    @extend_schema(responses=FeedbackResponseSerializer)
    def get(self, request, job_id):
        return self.handle_feedback(request, job_id)

    @extend_schema(request=VoteSerializer,responses=FeedbackResponseSerializer)
    def post(self, request, job_id):
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.handle_feedback(request, job_id, serializer.validated_data["value"])
