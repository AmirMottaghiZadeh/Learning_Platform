"""Who may do what in the panel. Superusers are admins; everyone else needs a
StaffRole row."""

from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

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


def role_of(user):
    if not (user.is_authenticated and user.is_active):
        return None
    if user.is_superuser:
        return StaffRole.ADMIN
    row = getattr(user, "site_role", None) if hasattr(user, "site_role") else None
    return row.role if row else None


def can(user, perm):
    granted = PERMS.get(role_of(user), set())
    return "*" in granted or perm in granted


def panel_required(perm=None):
    """A panel view: needs a signed-in staff user, and `perm` when given."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if role_of(request.user) is None:
                from apps.manage.views import login_url

                return redirect(login_url(request.get_full_path()))
            if perm and not can(request.user, perm):
                return render(request, "panel/forbidden.html", status=403)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
