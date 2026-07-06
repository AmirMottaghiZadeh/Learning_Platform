from django.db import transaction

from apps.ai_data_pipeline.models import AIDataChangeHistory
from apps.ai_data_pipeline.appliers.apply_changes import _model_for_table


def rollback_change_history(*, history_ids, rolled_back_by=""):
    rolled_back = 0
    with transaction.atomic():
        for history in AIDataChangeHistory.objects.select_for_update().filter(id__in=history_ids).order_by("-id"):
            model = _model_for_table(history.table_name)
            instance = model.objects.select_for_update().get(pk=history.record_id)
            setattr(instance, history.field_name, history.old_value)
            instance.save(update_fields=[history.field_name])
            history.rollback_batch_id = rolled_back_by or "manual"
            history.save(update_fields=["rollback_batch_id"])
            rolled_back += 1
    return rolled_back
