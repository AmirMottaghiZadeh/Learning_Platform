"""Routes the site's domains to the website urlconf, redirects www to the bare
domain, applies redirects an editor set up and the maintenance page."""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render

SITE_URLCONF = "config.urls_site"
# Paths that stay reachable while the site is in maintenance mode.
OPEN_PREFIXES = ("/panel/", "/ops/", "/pay/", "/static/", "/media/", "/account/")


class SiteHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host.startswith("www.") and host[4:] in settings.SITE_HOSTS:
            target = f"{request.scheme}://{host[4:]}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(target)
        if host in settings.SITE_HOSTS:
            request.urlconf = SITE_URLCONF
            request.is_site = True
        response = self.get_response(request)
        if getattr(request, "is_site", False) and response.status_code == 404:
            moved = self._redirect(request)
            if moved is not None:
                return moved
        return response

    @staticmethod
    def _redirect(request):
        from .models import Redirect

        path = request.path
        for candidate in {path, path.rstrip("/") or "/", path.rstrip("/") + "/"}:
            row = Redirect.objects.filter(from_path=candidate, is_active=True).first()
            if row:
                Redirect.objects.filter(pk=row.pk).update(hits=row.hits + 1)
                cls = HttpResponsePermanentRedirect if row.permanent else HttpResponseRedirect
                return cls(row.to_url)
        return None


class SiteMaintenanceMiddleware:
    """Shows the maintenance page to visitors while the setting is on. Runs
    after authentication so signed-in staff still see the site."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "is_site", False) and not request.path.startswith(OPEN_PREFIXES):
            from .models import SiteSettings

            site = SiteSettings.get()
            if site.maintenance_mode and not (request.user.is_authenticated and request.user.is_staff):
                return render(request, "website/maintenance.html", {"site": site}, status=503)
        return self.get_response(request)
