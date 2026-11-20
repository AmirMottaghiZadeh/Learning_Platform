"""Shared console capabilities for active platform role assignments.

Do not copy roles into Django's staff/superuser flags: revocation and expiry
must take effect on the next request, including an existing browser session.
"""

from .models import Role
from .services import active_role_keys


def has_role(user, *keys):
    return bool(
        user and user.is_authenticated and user.is_active
        and set(active_role_keys(user)).intersection(keys)
    )


def platform_admin(user):
    return bool(
        user and user.is_authenticated and user.is_active
        and (user.is_superuser or has_role(user, Role.PLATFORM_ADMIN))
    )


def billing_admin(user):
    return platform_admin(user) or has_role(user, Role.BILLING_ADMIN)
