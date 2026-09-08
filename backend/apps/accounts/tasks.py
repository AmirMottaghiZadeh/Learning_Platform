"""Account background work.

SMTP is a third-party dependency with unbounded latency. Keeping it in the
request meant a slow mail host stalled a web worker and a transient failure was
lost, so delivery moved behind the queue with a bounded retry budget.
"""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from apps.core.celery_tasks import PlatformTask


logger = logging.getLogger(__name__)


@shared_task(base=PlatformTask, bind=True, name="accounts.send_password_reset_email")
def send_password_reset_email_task(self, user_id):
    """Deliver one password-reset email, retrying transient SMTP failures."""
    from .services import send_password_reset_email

    user = (
        get_user_model()
        .objects.filter(pk=user_id, is_active=True)
        .first()
    )
    if user is None:
        logger.info("Skipping password-reset email for missing user_id=%s", user_id)
        return False
    if not user.has_usable_password():
        return False

    try:
        send_password_reset_email(user)
    except Exception as exc:
        self.retry_with_backoff(exc)
    return True
