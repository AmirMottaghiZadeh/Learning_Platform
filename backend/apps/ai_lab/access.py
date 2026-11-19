from types import SimpleNamespace

from django.conf import settings

from apps.accounts.access import platform_admin
from apps.billing.enforcement import require_feature
from apps.core.exceptions import PlatformAPIError
from .release import cohort


def allowed(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if settings.AI_LAB_LOCAL_LEXICAL_PILOT:
        return settings.ENVIRONMENT == "local" and platform_admin(user)
    return (
        platform_admin(user)
        or str(user.pk) in settings.AI_LAB_USER_IDS
        or (settings.AI_LAB_PUBLIC_ENABLED and not hasattr(user, "guest_account"))
        or cohort(user)
    )


def require_search_plan(user):
    """Plan access is separate from rollout eligibility and the credit wallet."""
    try:
        require_feature(SimpleNamespace(user=user), "smart_search")
    except PlatformAPIError as exc:
        if exc.code == "PREMIUM_REQUIRED":
            raise PlatformAPIError(
                "پلن فعلی شما شامل سرچ هوشمند نیست؛ پلن یا محصول دارای این قابلیت را تهیه کنید.",
                code=exc.code, status_code=exc.status_code, details=exc.details,
            ) from None
        raise
