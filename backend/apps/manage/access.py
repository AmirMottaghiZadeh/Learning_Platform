"""Who may enter the admin, and which of its modules.

The admin joins three tools that each kept their own rule, and keeps them:
the sales tools are for superusers, the data-quality desk for staff, and the
site's content for anyone with a site role (apps.website.permissions).
"""

from apps.website.permissions import can as site_can
from apps.website.permissions import role_of


def is_super(user):
    return bool(user.is_authenticated and user.is_active and user.is_superuser)


def is_operator(user):
    """The data-quality desk's rule: active staff."""
    return bool(user.is_authenticated and user.is_active and user.is_staff)


def has_site_role(user):
    return role_of(user) is not None


def can_enter(user):
    return is_super(user) or is_operator(user) or has_site_role(user)


def site(perm):
    """A rule for a site page: the role's permission `perm`."""
    return lambda user: site_can(user, perm)


def site_admin(user):
    return site_can(user, "*")


def anyone(user):
    return can_enter(user)
