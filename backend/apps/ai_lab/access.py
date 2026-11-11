from django.conf import settings

from apps.accounts.access import platform_admin
from .release import cohort


def allowed(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    return platform_admin(user) or str(user.pk) in settings.AI_LAB_USER_IDS or cohort(user)
