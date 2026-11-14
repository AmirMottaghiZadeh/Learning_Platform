"""Email possession verified by a one-use HMAC code; SMTP never logs the code."""
from datetime import timedelta
import hashlib
import hmac
import logging
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from apps.core import ratelimit
from .models import EmailLoginIdentity, EmailOneTimeCode, LearnerProfile, SecurityAuditEvent
from .otp import OtpError
from .services import _request_metadata, ensure_default_learner_role, record_security_event

logger = logging.getLogger(__name__)


def normalized(email):
    return email.strip().lower()


def _hash(email, code):
    return hmac.new(settings.SECRET_KEY.encode(),f"email-login:{email}:{code}".encode(),hashlib.sha256).hexdigest()


def _require_enabled():
    if not settings.AUTH_EMAIL_OTP_ENABLED:
        raise OtpError("ورود ایمیلی فعلاً فعال نیست.",code="EMAIL_OTP_DISABLED",status=503)


@sensitive_variables()
def request_code(email, *, request=None):
    _require_enabled()
    email=normalized(email);now=timezone.now();limits=ratelimit.current().otp
    code="".join(secrets.choice("0123456789") for _ in range(max(6,settings.EMAIL_OTP_CODE_LENGTH)))
    with transaction.atomic():
        identity,_=EmailLoginIdentity.objects.get_or_create(email=email)
        identity=EmailLoginIdentity.objects.select_for_update().get(pk=identity.pk)
        recent=list(identity.codes.filter(created_at__gte=now-timedelta(days=1)))
        if recent:
            wait=limits["resend_seconds"]-(now-recent[0].created_at).total_seconds()
            if wait>0:
                raise OtpError("برای ارسال کد تازه کمی صبر کنید.",code="OTP_TOO_SOON",status=429,details={"retry_after":int(wait)+1})
        window=[row for row in recent if (now-row.created_at).total_seconds()<limits["window_seconds"]]
        if len(window)>=limits["max_per_phone_per_window"] or len(recent)>=limits["max_per_phone_per_day"]:
            raise OtpError("برای این ایمیل کد زیادی درخواست شده است؛ کمی بعد دوباره تلاش کنید.",code="OTP_WINDOW_LIMIT",status=429)
        ip=_request_metadata(request)["ip_address"]
        if ip and EmailOneTimeCode.objects.filter(ip_address=ip,created_at__gte=now-timedelta(seconds=limits["window_seconds"])).count()>=limits["max_per_ip_per_window"]:
            raise OtpError("از این شبکه کد زیادی درخواست شده است.",code="OTP_IP_LIMIT",status=429)
        identity.codes.filter(consumed_at__isnull=True).update(consumed_at=now)
        row=EmailOneTimeCode.objects.create(identity=identity,code_hash=_hash(email,code),
            expires_at=now+timedelta(seconds=settings.EMAIL_OTP_TTL_SECONDS),ip_address=ip)
    try:
        # A console backend prints mail bodies, so refuse it for login secrets.
        if settings.EMAIL_BACKEND.endswith(("console.EmailBackend","filebased.EmailBackend")):
            raise ValueError
        message=EmailMultiAlternatives("کد ورود به فارمنتا",f"کد ورود شما به فارمنتا: {code}\nاین کد فقط یک بار قابل استفاده است و تا {settings.EMAIL_OTP_TTL_SECONDS//60} دقیقه اعتبار دارد.\nاگر شما درخواست نداده‌اید، این پیام را نادیده بگیرید.",settings.DEFAULT_FROM_EMAIL,[email])
        if message.send(fail_silently=False)!=1:
            raise ValueError
    except Exception:
        row.delete()
        logger.warning("email_otp_delivery_failed")
        raise OtpError("ارسال کد ایمیلی انجام نشد؛ کمی بعد دوباره تلاش کنید.",code="EMAIL_SEND_FAILED",status=503) from None
    record_security_event(SecurityAuditEvent.OTP_SENT,request=request,metadata={"channel":"email"})
    return row


@sensitive_variables()
def verify_code(email, code, *, request=None):
    _require_enabled();email=normalized(email)
    code=code.strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789"))
    now=timezone.now()
    with transaction.atomic():
        row=EmailOneTimeCode.objects.select_for_update().filter(identity_id=email,consumed_at__isnull=True).first()
        if row is None or row.expires_at<=now:
            raise OtpError("کد منقضی شده یا معتبر نیست؛ کد تازه بخواهید.",code="OTP_EXPIRED")
        if row.attempts>=settings.OTP_MAX_ATTEMPTS:
            raise OtpError("تعداد تلاش‌ها تمام شده است؛ کد تازه بخواهید.",code="OTP_LOCKED")
        matched=hmac.compare_digest(row.code_hash,_hash(email,code))
        if matched:row.consumed_at=now
        else:row.attempts+=1
        row.save(update_fields=["consumed_at","attempts"])
    if not matched:
        raise OtpError("کد واردشده درست نیست.",code="OTP_INVALID")
    with transaction.atomic():
        identity=EmailLoginIdentity.objects.select_for_update().get(pk=email)
        users=list(get_user_model().objects.filter(email__iexact=email)[:2])
        if len(users)>1 or (users and not users[0].is_active):
            raise OtpError("ورود به این حساب ممکن نیست؛ با پشتیبانی تماس بگیرید.",code="EMAIL_ACCOUNT_UNAVAILABLE")
        created=not users
        user=users[0] if users else get_user_model().objects.create_user(username="email_"+secrets.token_hex(16),email=email)
        LearnerProfile.objects.get_or_create(user=user)
        ensure_default_learner_role(user)
        identity.verified_at=now;identity.save(update_fields=["verified_at"])
    return user,created
