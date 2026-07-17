import logging
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils import timezone
from rest_framework.authtoken.models import Token


logger = logging.getLogger(__name__)


def issue_auth_token(user):
    """Return a currently valid token, rotating an expired token if necessary."""
    token, created = Token.objects.get_or_create(user=user)
    if not created and token.created + timedelta(hours=settings.AUTH_TOKEN_TTL_HOURS) <= timezone.now():
        token.delete()
        token = Token.objects.create(user=user)
    return token


def password_reset_url_for_user(user):
    """Build the public frontend URL that collects the new password."""
    parts = urlsplit(settings.PASSWORD_RESET_FRONTEND_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        {
            "reset_uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "reset_token": default_token_generator.make_token(user),
        }
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def send_password_reset_email(user):
    """Send a reset email without exposing account existence to API clients."""
    reset_url = password_reset_url_for_user(user)
    message = (
        "برای تعیین کلمه عبور جدید Pharmexa، از پیوند زیر استفاده کنید:\n\n"
        f"{reset_url}\n\n"
        f"این پیوند تا {settings.PASSWORD_RESET_TIMEOUT // 3600} ساعت معتبر است و "
        "بعد از استفاده یا تغییر کلمه عبور نامعتبر می‌شود. اگر این درخواست را شما ثبت نکرده‌اید، "
        "می‌توانید این ایمیل را نادیده بگیرید."
    )
    send_mail(
        subject="Pharmexa password reset",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return reset_url


def user_from_reset_uid(uidb64):
    try:
        return get_user_model().objects.get(
            pk=force_str(urlsafe_base64_decode(uidb64))
        )
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        return None
    except get_user_model().DoesNotExist:
        return None


def send_password_reset_emails_for_email(email):
    """Attempt delivery for matching active accounts and return no account details."""
    users = get_user_model().objects.filter(email__iexact=email, is_active=True)
    for user in users:
        if not user.has_usable_password():
            continue
        try:
            send_password_reset_email(user)
        except Exception:
            logger.exception("Password-reset email delivery failed for user_id=%s", user.pk)
