"""Website capabilities from legacy site roles and active platform roles."""

from functools import wraps

from django.shortcuts import redirect, render

from apps.accounts.access import billing_admin
from apps.accounts.models import Role
from apps.accounts.services import active_role_keys
from .models import StaffRole

EDITORIAL = {
    "dashboard.view", "post.create", "post.view_all", "post.edit_all", "post.publish", "post.delete",
    "page.manage", "taxonomy.manage", "media.upload", "media.manage", "comment.moderate",
    "announcement.manage", "download.manage", "content.manage", "menu.manage", "seo.manage",
    "subscriber.view", "contact.view", "orders.view",
}
PERMS = {
    StaffRole.ADMIN: {"*"},
    StaffRole.EDITOR: EDITORIAL,
    StaffRole.AUTHOR: {"dashboard.view", "post.create", "post.edit_own", "media.upload"},
    StaffRole.SUPPORT: {"dashboard.view", "comment.moderate", "contact.view", "subscriber.view", "orders.view"},
}


def roles_of(user):
    if not (user.is_authenticated and user.is_active):
        return set()
    if user.is_superuser:
        return {StaffRole.ADMIN}
    keys = set(active_role_keys(user))
    if Role.PLATFORM_ADMIN in keys:
        return {StaffRole.ADMIN}
    roles = set()
    row = getattr(user, "site_role", None)
    if row:
        roles.add(row.role)
    if Role.CONTENT_EDITOR in keys:
        roles.add(StaffRole.EDITOR)
    if Role.SUPPORT_AGENT in keys:
        roles.add(StaffRole.SUPPORT)
    return roles


def role_of(user):
    roles = roles_of(user)
    return next((role for role in (StaffRole.ADMIN, StaffRole.EDITOR, StaffRole.SUPPORT, StaffRole.AUTHOR) if role in roles), None)


def can(user, perm):
    if perm == "orders.view" and billing_admin(user):
        return True
    granted = set().union(*(PERMS.get(role, set()) for role in roles_of(user)))
    return "*" in granted or perm in granted


def panel_required(perm=None):
    """A panel view needs site access, or the given service capability."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if role_of(request.user) is None and not (perm and can(request.user, perm)):
                from apps.manage.views import login_url

                return redirect(login_url(request.get_full_path()))
            if perm and not can(request.user, perm):
                return render(request, "panel/forbidden.html", status=403)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
