"""Question-scoped, thread-safe HTTP pool; no automatic retries or stored auth."""
from contextlib import contextmanager
from contextvars import ContextVar
import os
import socket
from threading import Timer
import httpx
from django.conf import settings

_pool = ContextVar("ai_search_httpx_pool", default=None)


@contextmanager
def response_drain(response):
    """Bound post-DONE HTTP/1.1 reads; an idle upstream cannot hold the answer."""
    stream = response.extensions.get("network_stream")
    raw_socket = stream.get_extra_info("socket") if stream is not None else None
    if response.http_version != "HTTP/1.1" or not isinstance(raw_socket, socket.socket):
        yield False
        return
    def abort():
        try: raw_socket.shutdown(socket.SHUT_RDWR)
        except OSError: pass
    timer = Timer(max(.05, settings.AI_LAB_HTTP_DRAIN_SECONDS), abort)
    timer.daemon = True
    timer.start()
    try: yield True
    finally: timer.cancel()


@contextmanager
def session():
    if not settings.AI_LAB_HTTP_POOL_ENABLED or _pool.get() is not None:
        yield
        return
    with httpx.Client(follow_redirects=False, timeout=90,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=4,
                                keepalive_expiry=settings.AI_LAB_HTTP_KEEPALIVE_SECONDS)) as client:
        token = _pool.set((os.getpid(), client))
        try:
            yield
        finally:
            _pool.reset(token)


@contextmanager
def client(timeout):
    pooled = _pool.get()
    if pooled is not None and pooled[0] == os.getpid():
        yield pooled[1]
    else:
        with httpx.Client(timeout=timeout, follow_redirects=False) as connection:
            yield connection


def pooled(function):
    from functools import wraps
    @wraps(function)
    def wrapped(*args, **kwargs):
        with session():
            return function(*args, **kwargs)
    return wrapped
