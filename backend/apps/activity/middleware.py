import hashlib
import logging

from django.conf import settings

from .models import ActivityEvent
from .services import SITE_SECTIONS

logger = logging.getLogger(__name__)


class SiteActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(request, "is_site", False) or request.method != "GET" or response.status_code != 200:
            return response
        match = getattr(request, "resolver_match", None)
        key = match.url_name if match else ""
        # Known public routes only; never store URLs, searches, form values or
        # support-message contents in analytics.
        aliases = {"blog_list": "blog", "post_detail": "post", "drugs_index": "drugs", "drug_detail": "drug", "login_code": "login", "set_password": "login"}
        key = aliases.get(key, key)
        if key in SITE_SECTIONS:
            device = getattr(request, "browser_device_id", "")
            visitor = hashlib.sha256((settings.SECRET_KEY + device).encode()).hexdigest() if device else ""
            try:
                ActivityEvent.objects.create(user=request.user if request.user.is_authenticated else None, source="site", section=key, action="view", visitor=visitor)
            except Exception:
                logger.exception("Could not record a site activity event")
        return response
