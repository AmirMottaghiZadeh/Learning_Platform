"""Throttling that stays correct when the API runs on more than one worker.

DRF's stock throttles keep their counters in the ``default`` cache. With the
per-process ``LocMemCache`` that used to be configured, every Gunicorn worker
kept its own counters, so the effective rate limit was multiplied by the worker
count and disappeared entirely on horizontal scale-out. These classes bind the
counters to the shared ``throttle`` cache instead, and refuse to silently open
abuse-sensitive endpoints when that shared store is unreachable.
"""

import logging

from django.conf import settings
from django.core.cache import caches
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)


logger = logging.getLogger(__name__)

THROTTLE_CACHE_ALIAS = "throttle"


class ThrottleBackendUnavailable(Exception):
    """The shared throttle counter store could not be reached."""


def throttle_cache():
    return caches[THROTTLE_CACHE_ALIAS]


def _fail_closed_scopes():
    return set(getattr(settings, "THROTTLE_FAIL_CLOSED_SCOPES", []))


class SharedCacheThrottleMixin:
    """Route throttle counters through the shared cache and handle outages."""

    cache = None

    def __init__(self):
        self.cache = throttle_cache()
        super().__init__()

    def _fails_closed(self, scope):
        return bool(scope) and scope in _fail_closed_scopes()

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except ThrottleBackendUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - exercised via broken cache
            scope = getattr(self, "scope", None)
            if self._fails_closed(scope):
                logger.error(
                    "Throttle store unavailable for fail-closed scope %s: %s",
                    scope,
                    exc,
                )
                self.history = []
                return False
            logger.warning(
                "Throttle store unavailable for scope %s, allowing request: %s",
                scope,
                exc,
            )
            return True

    def wait(self):
        try:
            return super().wait()
        except Exception:  # pragma: no cover - defensive
            return None


class DistributedAnonRateThrottle(SharedCacheThrottleMixin, AnonRateThrottle):
    pass


class DistributedUserRateThrottle(SharedCacheThrottleMixin, UserRateThrottle):
    pass


class DistributedScopedRateThrottle(SharedCacheThrottleMixin, ScopedRateThrottle):
    def _fails_closed(self, scope):
        # ScopedRateThrottle resolves ``self.scope`` from the view during
        # allow_request; on an early cache failure it may still be unset.
        return super()._fails_closed(getattr(self, "scope", None))


class BurstRateThrottle(SharedCacheThrottleMixin, SimpleRateThrottle):
    scope = "burst"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SustainedRateThrottle(BurstRateThrottle):
    scope = "sustained"
