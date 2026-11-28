"""The single place application code hands work to the queue.

``CELERY_TASK_ALWAYS_EAGER`` is the platform's declared answer to "may this run
in-process?". Routing every enqueue through here makes that setting
authoritative at run time, so local development and tests behave predictably
without depending on whether a broker URL happens to be exported.
"""

from django.conf import settings


def enqueue(task, *args, **kwargs):
    """Queue the task, or run it inline where in-process execution is declared."""
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return task.apply(args=args, kwargs=kwargs)
    return task.delay(*args, **kwargs)
