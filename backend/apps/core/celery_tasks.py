"""Shared task base class carrying the platform retry policy.

Every background task inherits the same contract:

* transient failures retry with exponential backoff plus jitter, so a
  dependency outage does not turn into a synchronized retry storm;
* the retry budget is bounded and read at run time, not frozen at import.
"""

import logging
import random

from celery import Task
from django.conf import settings


logger = logging.getLogger(__name__)


def retry_delay_seconds(retries):
    """Exponential backoff with jitter for the given retry count."""
    base = settings.CELERY_TASK_RETRY_BACKOFF_SECONDS
    maximum = settings.CELERY_TASK_RETRY_BACKOFF_MAX_SECONDS
    delay = min(base * (2 ** max(0, retries)), maximum)
    return max(1, int(random.uniform(delay / 2, delay)))


class PlatformTask(Task):
    """Base task with bounded retries and jittered backoff."""

    acks_late = True
    reject_on_worker_lost = True
    max_retries = None  # resolved from settings at run time

    def retry_with_backoff(self, exc):
        """Retry the task, or let it fail terminally once the budget is spent."""
        retries = self.request.retries if self.request else 0
        raise self.retry(
            exc=exc,
            countdown=retry_delay_seconds(retries),
            max_retries=settings.CELERY_TASK_MAX_RETRIES,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log the terminal failure so it is not lost in worker noise."""
        logger.error(
            "Task %s failed terminally (task_id=%s): %s",
            self.name or self.__class__.__name__,
            task_id,
            exc,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
