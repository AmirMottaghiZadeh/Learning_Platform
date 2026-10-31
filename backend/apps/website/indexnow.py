"""IndexNow: tells the search engines that take part -- Bing, Yandex, Naver,
Seznam, and through Bing the search behind ChatGPT, Copilot and DuckDuckGo --
that a page is new or has changed, so it is crawled within minutes instead of
whenever their crawler next comes by. Google does not take part; it reads the
sitemap.

Off until settings.INDEXNOW_KEY is set. The key is published at
/<key>.txt (views_public.indexnow_key), which is how the engines check that
a submission comes from the site's owner.
"""

import json
import logging
import threading
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction

from . import services

logger = logging.getLogger(__name__)

ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10_000  # the protocol's limit per request
TIMEOUT_SECONDS = 10


def enabled():
    from .models import SiteSettings

    return bool(settings.INDEXNOW_KEY) and not SiteSettings.get().noindex_site


def submit(paths):
    """Submit the site's paths ("/drugs/amoxicillin/") now. Returns how many
    URLs the endpoint accepted; a failure is logged, never raised -- this is a
    courtesy to the search engines, not something a page save may fail on."""
    if not enabled():
        return 0
    urls = sorted({services.absolute(path) for path in paths})
    key = settings.INDEXNOW_KEY
    accepted = 0
    for start in range(0, len(urls), BATCH):
        batch = urls[start:start + BATCH]
        body = json.dumps({
            "host": urlsplit(services.absolute("/")).hostname,
            "key": key,
            "keyLocation": services.absolute(f"/{key}.txt"),
            "urlList": batch,
        }).encode()
        request = urllib.request.Request(
            ENDPOINT, data=body, method="POST", headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            logger.warning("indexnow: rejected %s URLs: HTTP %s", len(batch), exc.code)
            continue
        except (urllib.error.URLError, OSError) as exc:
            logger.warning("indexnow: cannot reach %s: %s", ENDPOINT, exc)
            break
        if status in (200, 202):
            accepted += len(batch)
        else:
            logger.warning("indexnow: unexpected HTTP %s for %s URLs", status, len(batch))
    if accepted:
        logger.info("indexnow: submitted %s URLs", accepted)
    return accepted


def notify(paths):
    """Submit once the current transaction commits, off the request: an
    editor's save never waits on, or fails because of, the endpoint."""
    paths = [path for path in paths if path]
    if not paths or not enabled():
        return
    transaction.on_commit(lambda: threading.Thread(target=submit, args=(paths,), daemon=True).start())
