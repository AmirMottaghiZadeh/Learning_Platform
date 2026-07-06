from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataSuggestion


def review_suggestions(*, suggestion_ids=None, batch_id=None, action, reviewed_by="", edited_value=None, risk_level=None):
    queryset = AIDataSuggestion.objects.all()
    if suggestion_ids:
        queryset = queryset.filter(id__in=suggestion_ids)
    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)
    if risk_level:
        queryset = queryset.filter(risk_level=risk_level)

    now = timezone.now()
    count = 0
    for suggestion in queryset:
        if suggestion.status == constants.SUGGESTION_STATUS_APPLIED:
            continue
        if action == "approve":
            suggestion.status = constants.SUGGESTION_STATUS_APPROVED
        elif action == "reject":
            suggestion.status = constants.SUGGESTION_STATUS_REJECTED
        elif action == "edit":
            if edited_value is None:
                raise ValueError("edited_value is required for edit action.")
            suggestion.suggested_value = edited_value
            suggestion.status = constants.SUGGESTION_STATUS_EDITED
        else:
            raise ValueError("Unsupported review action.")
        suggestion.reviewed_at = now
        suggestion.reviewed_by = reviewed_by
        suggestion.save(update_fields=["status", "suggested_value", "reviewed_at", "reviewed_by", "updated_at"])
        count += 1
    return count
