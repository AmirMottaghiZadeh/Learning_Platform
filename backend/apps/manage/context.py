from django.conf import settings
from django.utils.functional import SimpleLazyObject

from . import nav


def shell(request):
    """The admin shell's rail, page column and command bar, on admin pages
    only -- built the first time a template reads it."""
    if not request.path.startswith("/manage/") or not request.user.is_authenticated:
        return {}
    return {
        "mg": SimpleLazyObject(lambda: nav.build(request)),
        "mg_env": settings.ENVIRONMENT,
        "mg_site_url": settings.SITE_PUBLIC_URL.rstrip("/"),
    }
