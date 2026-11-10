from django.urls import path
from .views import ActiveView, AskView, LabStatusView, ResultView

urlpatterns = [
    path("ai-lab/status/", LabStatusView.as_view(), name="ai-lab-status"),
    path("ai-lab/active/", ActiveView.as_view(), name="ai-lab-active"),
    path("ai-lab/ask/", AskView.as_view(), name="ai-lab-ask"),
    path("ai-lab/results/<uuid:job_id>/", ResultView.as_view(), name="ai-lab-result"),
]
