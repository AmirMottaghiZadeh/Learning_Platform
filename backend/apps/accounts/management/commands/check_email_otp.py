from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand, CommandError

from config.email_config import SMTP_BACKEND, smtp_configuration_problem


class Command(BaseCommand):
    help = "Check the configured email OTP SMTP connection without sending a message."

    def handle(self, *args, **options):
        if not settings.AUTH_EMAIL_OTP_ENABLED:
            raise CommandError("AUTH_EMAIL_OTP_ENABLED is false.")
        if settings.EMAIL_BACKEND != SMTP_BACKEND:
            raise CommandError("Set EMAIL_BACKEND to Django's SMTP backend.")
        problem = smtp_configuration_problem(settings)
        if problem:
            raise CommandError(problem)

        try:
            with get_connection(fail_silently=False):
                pass
        except OSError as error:
            status = getattr(error, "smtp_code", None)
            detail = f", SMTP status {status}" if isinstance(status, int) else ""
            raise CommandError(f"SMTP connection failed ({type(error).__name__}{detail}).") from None

        self.stdout.write(self.style.SUCCESS("SMTP connection check passed. No email was sent."))
