"""Admin entry and navigation use the same capabilities as each service."""

from apps.accounts.access import billing_admin, platform_admin
from apps.data_quality_center.access import can_view as is_operator
from apps.data_quality_center.access import can_review as quality_review

from apps.website.permissions import can as site_can
from apps.website.permissions import role_of


def is_super(user):
    return bool(user.is_authenticated and user.is_active and user.is_superuser)


def has_site_role(user):
    return role_of(user) is not None


def can_enter(user):
    return platform_admin(user) or billing_admin(user) or is_operator(user) or has_site_role(user) or support(user)


def support(user):
    from apps.support.services import can_support

    return can_support(user)


def site(perm):
    """A rule for a site page: the role's permission `perm`."""
    return lambda user: site_can(user, perm)


def site_admin(user):
    return site_can(user, "*")


def anyone(user):
    return can_enter(user)
