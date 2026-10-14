"""The calls content views make before serving something sold: whether the
learner's plans include the feature (and count the use when it is capped),
and whether a content feature fences this content off.

Inert unless BILLING_ENFORCEMENT_ENABLED, and never applied to staff, so
operators always see everything.
"""

from django.conf import settings

from apps.core.exceptions import PlatformAPIError
from apps.lessons.data.study_topics import STUDY_TOPICS

from . import services
from .catalog import SCOPE_ATC_PREFIX, SCOPE_TOPIC_CATEGORY

_TOPIC_CATEGORY = {t["key"]: t["category"] for t in STUDY_TOPICS}


def _applies(request):
    user = getattr(request, "user", None)
    return (
        settings.BILLING_ENFORCEMENT_ENABLED
        and user is not None
        and user.is_authenticated
        and not user.is_staff
    )


def require_feature(request, key, *, item=None, consume=False):
    """Raise a 402 unless the learner may use `key`; with `consume`, count
    this use of `item` against the feature's cap."""
    if not _applies(request):
        return
    access = services.check_feature(request.user, key, item=item, consume=consume)
    if access.allowed:
        return
    if access.reason == "quota":
        raise PlatformAPIError(
            "You have used this feature's allowance for now.",
            code="QUOTA_EXCEEDED",
            status_code=402,
            details={"feature": key, "limit": access.limit, "period": access.period, "used": access.used},
        )
    raise PlatformAPIError(
        "Your plan does not include this feature.",
        code="PREMIUM_REQUIRED",
        status_code=402,
        details={"feature": key},
    )


def _require_content(request, scope_type, value):
    if not _applies(request):
        return
    fences = services.content_lock(request.user, scope_type, value)
    if fences:
        raise PlatformAPIError(
            "This content is part of a plan you do not have.",
            code="PREMIUM_REQUIRED",
            status_code=402,
            details={"feature": fences[0].key, "features": [f.key for f in fences]},
        )


def require_atc_content(request, atc_code):
    _require_content(request, SCOPE_ATC_PREFIX, atc_code)


def require_topic_content(request, topic_key):
    """A study topic's content, fenced by its category."""
    _require_content(request, SCOPE_TOPIC_CATEGORY, _TOPIC_CATEGORY.get(topic_key, ""))
