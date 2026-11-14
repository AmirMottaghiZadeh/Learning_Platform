from django.urls import path
from apps.ai_feedback.views import FeedbackView
from .views import ActiveView, AskView, LabStatusView, ResultView
from .stream_views import StreamView, CancelView

urlpatterns = [
    path("ai-lab/results/<uuid:job_id>/stream/", StreamView.as_view(), name="ai-lab-stream"),
    path("ai-lab/results/<uuid:job_id>/cancel/", CancelView.as_view(), name="ai-lab-cancel"),
    path("ai-lab/results/<uuid:job_id>/feedback/", FeedbackView.as_view(), name="ai-lab-feedback"),
    path("ai-lab/status/", LabStatusView.as_view(), name="ai-lab-status"),
    path("ai-lab/active/", ActiveView.as_view(), name="ai-lab-active"),
    path("ai-lab/ask/", AskView.as_view(), name="ai-lab-ask"),
    path("ai-lab/results/<uuid:job_id>/", ResultView.as_view(), name="ai-lab-result"),
]
