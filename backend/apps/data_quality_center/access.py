"""Capabilities shared by the quality desk, workflow and admin navigation."""

from apps.accounts.services import user_has_platform_permission


def _staff(user):
    return bool(user and user.is_authenticated and user.is_active and user.is_staff)


def can_approve(user):
    # Approval in this console also applies the reviewed summaries atomically.
    return user_has_platform_permission(user, "accounts.approve_data_quality_suggestion")


def can_review(user):
    return can_approve(user) or user_has_platform_permission(user, "accounts.review_data_quality_suggestion")


def can_edit(user):
    return _staff(user) or can_review(user)


def can_view(user):
    return can_edit(user) or user_has_platform_permission(user, "accounts.view_data_quality_center")


def can_revert(user):
    return can_approve(user) and user_has_platform_permission(user, "accounts.apply_data_quality_change")
