"""Optional local SMTP file. Environment values take precedence in settings."""
import json
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def private_email_settings(path):
    if not path:
        return {}
    try:
        file = Path(path)
        if file.stat().st_mode & 0o077:
            raise ValueError
        values = json.loads(file.read_text())
        allowed = {"EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD",
                   "EMAIL_USE_TLS", "EMAIL_USE_SSL", "DEFAULT_FROM_EMAIL"}
        if not isinstance(values,dict) or set(values)-allowed:
            raise ValueError
        return values
    except (OSError,ValueError):
        raise ImproperlyConfigured("Private email configuration is unavailable or has unsafe permissions.") from None
