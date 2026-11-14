import logging
from django.conf import settings
from django.utils.crypto import salted_hmac
from apps.core.exceptions import PlatformAPIError
from .models import SearchAnswer, SearchFeedback

logger = logging.getLogger(__name__)


def user_key(user):
    return salted_hmac("smart-search-feedback-owner", str(user.pk), algorithm="sha256").hexdigest()


def save_answer(job_id, user, question, result):
    if not settings.AI_LAB_FEEDBACK_ENABLED:
        return False
    try:
        record, created = SearchAnswer.objects.get_or_create(pk=job_id, defaults={"user_key": user_key(user), "question": question,
            "question_types": list(dict.fromkeys(p.get("intent", "general") for p in result.get("parts", []))) or ["out_of_scope"],
            "result": result, "model": settings.AI_LAB_MODEL})
        return created or (record.user_key == user_key(user) and record.question == question and record.result == result)
    except Exception:
        # An independent store outage must neither leak connection details nor discard a clinical answer.
        logger.warning("ai_feedback_answer_store_unavailable")
        return False


def owned_answer(job_id, user):
    if not settings.AI_LAB_FEEDBACK_ENABLED:
        raise PlatformAPIError("ثبت بازخورد فعلاً در دسترس نیست.", code="FEEDBACK_UNAVAILABLE", status_code=503)
    try:
        return SearchAnswer.objects.get(pk=job_id, user_key=user_key(user))
    except SearchAnswer.DoesNotExist:
        from apps.ai_lab.models import SearchRun
        from apps.ai_lab.job_store import decode
        from apps.ai_lab.provider import ProviderError
        run = SearchRun.objects.filter(pk=job_id, owner_id=user.pk, status="complete").first()
        if run is None:
            raise PlatformAPIError("پاسخ پیدا نشد.", code="NOT_FOUND", status_code=404) from None
        try:
            completed, payload = decode(run.encrypted_result), decode(run.encrypted_payload)
        except ProviderError:
            raise PlatformAPIError("ثبت بازخورد فعلاً در دسترس نیست.",code="FEEDBACK_UNAVAILABLE",status_code=503) from None
        if not isinstance(completed.get("result"), dict) or not isinstance(payload.get("question"), str):
            raise PlatformAPIError("پاسخ پیدا نشد.",code="NOT_FOUND",status_code=404)
        if not save_answer(job_id,user,payload["question"],completed["result"]):
            raise PlatformAPIError("ثبت بازخورد فعلاً در دسترس نیست.",code="FEEDBACK_UNAVAILABLE",status_code=503)
        return SearchAnswer.objects.get(pk=job_id, user_key=user_key(user))


def rating(answer):
    return SearchFeedback.objects.filter(answer=answer).values_list("value", flat=True).first()


def rate(answer, value):
    record, _ = SearchFeedback.objects.update_or_create(answer=answer, defaults={"value": value})
    return record.value
