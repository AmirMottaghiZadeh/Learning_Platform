"""`manage.py check --deploy` warnings for SMS sign-up: without sms.ir set
up, codes are only written to the log, so nobody can sign up."""

from django.conf import settings
from django.core.checks import Tags, Warning, register


@register(Tags.security, deploy=True)
def sms_configured(app_configs, **kwargs):
    if settings.SMS_BACKEND == "console":
        return [Warning(
            "SMS codes are written to the log, not sent: sign-up and password reset by SMS won't reach anyone.",
            hint="Set SMSIR_API_KEY and SMSIR_OTP_TEMPLATE_ID (and SMSIR_OTP_PARAMETER if not CODE).",
            id="accounts.W001",
        )]
    if settings.SMS_BACKEND == "smsir" and not settings.SMSIR_OTP_TEMPLATE_ID:
        return [Warning(
            "SMSIR_API_KEY is set but SMSIR_OTP_TEMPLATE_ID is not: no code can be sent.",
            hint="Set SMSIR_OTP_TEMPLATE_ID to the id of the approved verify template.",
            id="accounts.W002",
        )]
    return []
