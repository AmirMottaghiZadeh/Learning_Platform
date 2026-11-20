"""Prepare the canonical search inside the process that will serve requests."""
import logging
import time

from django.conf import settings

from apps.uptodate import services as utd

logger = logging.getLogger(__name__)


def warm_search():
    if not settings.AI_LAB_ENABLED or not settings.AI_LAB_PREWARM_ENABLED:
        return False
    started = time.monotonic()
    try:
        if not utd.is_available():
            logger.warning("ai_lab_search_warmup_unavailable")
            return False
        # This loads the shared title/catalog/tagging caches, not an LLM answer.
        utd.search_page("nocturnal enuresis", limit=30, offset=0, section="")
    except Exception:
        # The reference may be temporarily unavailable. Never log connection secrets.
        logger.warning("ai_lab_search_warmup_failed")
        return False
    logger.info("ai_lab_search_warmup_complete elapsed_ms=%s", round((time.monotonic() - started) * 1000))
    return True
