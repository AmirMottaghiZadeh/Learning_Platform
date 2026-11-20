"""SMTP configuration and its optional local settings file."""
import json
from email.utils import parseaddr
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email

SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
LOCAL_FROM_EMAIL = "no-reply@pharmexa.local"


def private_email_settings(path):
    if not path:
        return {}
    try:
        file = Path(path)
        if file.stat().st_mode & 0o077:
            raise ValueError
        values = json.loads(file.read_text())
        allowed = {
            "EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER",
            "EMAIL_HOST_PASSWORD", "EMAIL_USE_TLS", "EMAIL_USE_SSL", "DEFAULT_FROM_EMAIL",
        }
        if not isinstance(values, dict) or set(values) - allowed:
            raise ValueError
        return values
    except (OSError, ValueError):
        raise ImproperlyConfigured("Private email configuration is unavailable or has unsafe permissions.") from None


def smtp_configuration_problem(settings):
    """Return an operator-facing message containing setting names only."""
    if not settings.EMAIL_HOST.strip():
        return "Set EMAIL_HOST to the SMTP server hostname."
    if not 1 <= settings.EMAIL_PORT <= 65535:
        return "Set EMAIL_PORT to a valid SMTP port."
    if settings.EMAIL_USE_SSL and settings.EMAIL_USE_TLS:
        return "Enable at most one of EMAIL_USE_SSL and EMAIL_USE_TLS."
    if bool(settings.EMAIL_HOST_USER) != bool(settings.EMAIL_HOST_PASSWORD):
        return "Set both EMAIL_HOST_USER and EMAIL_HOST_PASSWORD for SMTP authentication."
    sender = parseaddr(settings.DEFAULT_FROM_EMAIL)[1]
    try:
        validate_email(sender)
    except ValidationError:
        return "Set DEFAULT_FROM_EMAIL to a valid SMTP sender."
    if sender.lower() == LOCAL_FROM_EMAIL:
        return "Set DEFAULT_FROM_EMAIL to the SMTP account's verified sender."
    return None
