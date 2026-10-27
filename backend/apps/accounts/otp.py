"""SMS one-time codes for signing up and for resetting a password.

The flows they serve:
- sign up: a new number gets a code; the correct code creates the account
  and signs it in, and the app then makes the user choose a password --
  every later sign-in is number + password, with no SMS;
- forgotten password: a registered number gets a code; the correct code
  signs the user in, and the app asks for a new password.

Codes are random digits, stored only as an HMAC keyed with SECRET_KEY,
valid for OTP_TTL_SECONDS, spent by their first correct use, and dead after
OTP_MAX_ATTEMPTS wrong ones. A number can be sent a new code at most every
OTP_RESEND_SECONDS, OTP_MAX_PER_PHONE_PER_WINDOW times in any
OTP_WINDOW_SECONDS (3 in 10 minutes) and OTP_MAX_PER_PHONE_PER_DAY times a
day; one address can ask for OTP_MAX_PER_IP_PER_WINDOW codes in that window,
more than a number may, since many phones share a carrier's address. With the
per-address request throttles, that is what keeps the SMS credit safe and a
number from being flooded.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import LearnerProfile, OneTimeCode, SecurityAuditEvent
from .services import _request_metadata, ensure_default_learner_role, record_security_event
from .sms import SmsSendError, mask, send_code

User = get_user_model()
logger = logging.getLogger(__name__)


class OtpError(Exception):
    """A request the code rules refuse. `code` is the API error code;
    `details` goes back to the client (e.g. how long to wait)."""

    def __init__(self, message, *, code, status=400, details=None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _hash(phone, purpose, code):
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, f"{phone}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()


def _new_code():
    length = max(4, settings.OTP_CODE_LENGTH)
    return "".join(secrets.choice("0123456789") for _ in range(length))


def _minutes(seconds):
    """«۴ دقیقه»: a wait in whole minutes, rounded up, in Persian digits."""
    minutes = max(1, -(-int(seconds) // 60))
    return str(minutes).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")) + " دقیقه"


def user_for_phone(phone):
    profile = LearnerProfile.objects.select_related("user").filter(phone=phone).first()
    return profile.user if profile else None


def request_code(phone, purpose, *, request=None):
    """Creates and sends a code for `phone`. Returns the OneTimeCode row.

    Sign-up refuses a number that already has a finished account (it signs
    in with its password instead); a number whose sign-up was never
    finished -- no password chosen yet -- may get a code again. Reset
    refuses a number with no account."""
    user = user_for_phone(phone)
    if purpose == OneTimeCode.SIGNUP and user is not None and user.has_usable_password():
        raise OtpError(
            "این شماره قبلاً ثبت‌نام کرده؛ با شماره و رمز عبور وارد شو.",
            code="PHONE_REGISTERED", status=409,
        )
    if purpose == OneTimeCode.RESET and (user is None or not user.is_active):
        raise OtpError("حسابی با این شماره پیدا نشد.", code="PHONE_NOT_REGISTERED", status=404)

    now = timezone.now()
    with transaction.atomic():
        # One request at a time per number, so two quick taps can't both
        # pass the resend check.
        recent = list(
            OneTimeCode.objects.select_for_update()
            .filter(phone=phone, created_at__gte=now - timedelta(days=1))
            .order_by("-created_at")
        )
        if recent:
            wait = settings.OTP_RESEND_SECONDS - (now - recent[0].created_at).total_seconds()
            if wait > 0:
                raise OtpError(
                    "کمی صبر کن و بعد کد تازه بخواه.",
                    code="OTP_TOO_SOON", status=429, details={"retry_after": int(wait) + 1},
                )
        window = settings.OTP_WINDOW_SECONDS
        in_window = [r for r in recent if (now - r.created_at).total_seconds() < window]
        if len(in_window) >= settings.OTP_MAX_PER_PHONE_PER_WINDOW:
            wait = window - (now - in_window[-1].created_at).total_seconds()
            raise OtpError(
                f"برای هر شماره در {_minutes(window)} حداکثر {settings.OTP_MAX_PER_PHONE_PER_WINDOW} کد فرستاده "
                f"می‌شود؛ {_minutes(wait)} دیگر دوباره امتحان کن.",
                code="OTP_WINDOW_LIMIT", status=429, details={"retry_after": int(wait) + 1},
            )
        if len(recent) >= settings.OTP_MAX_PER_PHONE_PER_DAY:
            raise OtpError(
                "امروز برای این شماره کد زیادی فرستاده شده؛ فردا دوباره امتحان کن.",
                code="OTP_DAILY_LIMIT", status=429,
            )
        ip_address = _request_metadata(request)["ip_address"]
        if ip_address:
            from_ip = list(
                OneTimeCode.objects.filter(ip_address=ip_address, created_at__gte=now - timedelta(seconds=window))
                .order_by("created_at")
                .values_list("created_at", flat=True)[: settings.OTP_MAX_PER_IP_PER_WINDOW]
            )
            if len(from_ip) >= settings.OTP_MAX_PER_IP_PER_WINDOW:
                wait = window - (now - from_ip[0]).total_seconds()
                raise OtpError(
                    f"از این شبکه کد زیادی خواسته شده؛ {_minutes(wait)} دیگر دوباره امتحان کن.",
                    code="OTP_IP_LIMIT", status=429, details={"retry_after": int(wait) + 1},
                )

        code = _new_code()
        row = OneTimeCode.objects.create(
            phone=phone,
            purpose=purpose,
            code_hash=_hash(phone, purpose, code),
            expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS),
            ip_address=ip_address,
        )
        # Older unused codes for the same purpose stop working: only the
        # newest SMS counts.
        OneTimeCode.objects.filter(phone=phone, purpose=purpose, consumed_at__isnull=True).exclude(
            pk=row.pk
        ).update(consumed_at=now)

    try:
        message_id = send_code(phone, code)
    except SmsSendError as exc:
        # The reason (missing setting, sms.ir's own message, unreachable) goes
        # to the log, so a 503 in production can be traced; never the code.
        logger.error("SMS code to %s not sent: %s", mask(phone), exc)
        # Not sent, so it mustn't count against the resend gap or daily cap.
        row.delete()
        raise OtpError(
            "ارسال پیامک ممکن نشد؛ چند لحظهٔ دیگر دوباره امتحان کن.",
            code="SMS_SEND_FAILED", status=503,
        ) from exc
    if message_id:
        OneTimeCode.objects.filter(pk=row.pk).update(provider_message_id=message_id[:64])
    record_security_event(
        SecurityAuditEvent.OTP_SENT,
        user=user,
        request=request,
        metadata={"phone": mask(phone), "purpose": purpose},
    )
    return row


def verify_code(phone, purpose, code, *, request=None):
    """Spends the newest live code for (phone, purpose) if `code` matches;
    otherwise counts the attempt and raises OtpError."""
    code = (code or "").strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    now = timezone.now()
    with transaction.atomic():
        row = (
            OneTimeCode.objects.select_for_update()
            .filter(phone=phone, purpose=purpose, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if row is None or row.expires_at <= now:
            raise OtpError("کد منقضی شده یا وجود ندارد؛ کد تازه بخواه.", code="OTP_EXPIRED")
        if row.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise OtpError("تعداد تلاش‌ها تمام شد؛ کد تازه بخواه.", code="OTP_LOCKED")
        matched = hmac.compare_digest(row.code_hash, _hash(phone, purpose, code))
        if matched:
            row.consumed_at = now
            row.save(update_fields=["consumed_at"])
        else:
            row.attempts += 1
            row.save(update_fields=["attempts"])
    # Raised only after the block commits: inside it, the error would roll
    # the attempt count back and wrong guesses would never add up.
    if not matched:
        left = settings.OTP_MAX_ATTEMPTS - row.attempts
        record_security_event(
            SecurityAuditEvent.OTP_FAILED,
            user=user_for_phone(phone),
            request=request,
            metadata={"phone": mask(phone), "purpose": purpose, "attempts": row.attempts},
        )
        raise OtpError(
            "کد درست نیست." if left else "کد درست نیست و تلاش‌ها تمام شد؛ کد تازه بخواه.",
            code="OTP_INVALID", details={"attempts_left": left},
        )
    return row


@transaction.atomic
def account_for_signup(phone):
    """The account a verified sign-up number signs into: the one it already
    has (a sign-up never finished with a password), or a new one with no
    usable password yet. Returns (user, created)."""
    user = user_for_phone(phone)
    if user is not None:
        return user, False
    username = phone if not User.objects.filter(username__iexact=phone).exists() else f"m{phone}"
    user = User.objects.create_user(username=username, email="")
    user.set_unusable_password()
    user.save(update_fields=["password"])
    ensure_default_learner_role(user)
    try:
        with transaction.atomic():
            LearnerProfile.objects.update_or_create(
                user=user,
                defaults={"phone": phone, "phone_verified_at": timezone.now(), "display_name": ""},
            )
    except IntegrityError:
        # The same number finished signing up in a parallel request.
        raise OtpError("این شماره همین حالا ثبت‌نام شد؛ دوباره وارد شو.", code="PHONE_REGISTERED", status=409)
    return user, True
