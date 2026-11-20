"""One bounded HTTPS keep-alive connection per worker thread, no redirects/replay."""
import http.client
import os
import ssl
import socket
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit

from django.conf import settings
from . import telemetry

_local = threading.local()


class ReadDeadline:
    """Abort a trickling header/body at the absolute deadline, not just idle I/O."""
    def __init__(self, sock, seconds):
        self.sock, self.lock = sock, threading.Lock()
        self.done = self.expired = False
        self.timer = threading.Timer(max(0, seconds), self.expire)
        self.timer.daemon = True
        self.timer.start()

    def expire(self):
        with self.lock:
            if self.done:
                return
            self.expired = True
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def cancel(self):
        with self.lock:
            self.done = True
            self.timer.cancel()


class Response:
    def __init__(self, owner, response, sock, expires, timeout, guard):
        self.owner, self.response, self.sock = owner, response, sock
        self.expires, self.timeout = expires, timeout
        self.guard = guard
        self.drained = False

    def __enter__(self):
        return self

    def read(self, limit):
        chunks, length = [], 0
        while length < limit:
            if self.guard.expired:
                raise TimeoutError()
            if self.response.isclosed():
                if self.response.length not in (None, 0):
                    raise http.client.IncompleteRead(b"", self.response.length)
                self.drained = True
                break
            remaining = self.expires - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            self.sock.settimeout(min(self.timeout, remaining))
            chunk = self.response.read1(min(65536, limit - length))
            if self.guard.expired:
                raise TimeoutError()
            if not chunk:
                if self.response.length not in (None, 0):
                    raise http.client.IncompleteRead(b"", self.response.length)
                self.drained = True
                break
            chunks.append(chunk)
            length += len(chunk)
        return b"".join(chunks)

    def __exit__(self, kind, value, traceback):
        self.guard.cancel()
        try:
            self.response.close()
        finally:
            if kind is not None or not self.drained or self.response.will_close or self.guard.expired:
                self.owner.close()
            else:
                self.owner.last_used = time.monotonic()


class HTTPSOpener:
    def __init__(self):
        self.connection = self.origin = None
        self.last_used = 0

    def close(self):
        if self.connection is not None:
            self.connection.close()
        self.connection = self.origin = None

    def open(self, request, *, timeout):
        parsed = urlsplit(request.full_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("HTTPS required")
        origin = (parsed.hostname, parsed.port or 443)
        started = time.monotonic()
        expires = started + timeout
        guard = None
        if (self.origin != origin or started - self.last_used >= settings.AI_LAB_HTTP_KEEPALIVE_SECONDS):
            self.close()
        try:
            telemetry.provider_connection(self.connection is not None and self.connection.sock is not None)
            if self.connection is None:
                self.connection = http.client.HTTPSConnection(origin[0], origin[1], timeout=timeout,
                                                               context=ssl.create_default_context())
                self.origin = origin
            self.connection.timeout = timeout
            if self.connection.sock is not None:
                self.connection.sock.settimeout(timeout)
            # Authorization is supplied anew on every call, never a client default.
            headers = dict(request.header_items())
            headers["Connection"] = "keep-alive"
            self.connection.request(request.get_method(), parsed.path or "/", body=request.data, headers=headers)
            remaining = expires - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            self.connection.sock.settimeout(min(timeout, remaining))
            sock = self.connection.sock
            guard = ReadDeadline(sock, remaining)
            response = self.connection.getresponse()
            if not 200 <= response.status < 300:
                status = response.status
                response.close()
                self.close()
                raise HTTPError(request.full_url, status, "Provider HTTP error", {}, None)
            return Response(self, response, sock, expires, timeout, guard)
        except Exception:
            # A stale keep-alive POST is never automatically replayed: the
            # provider might already have billed/processed it.
            self.close()
            if guard is not None:
                guard.cancel()
            raise


def opener():
    pid = os.getpid()
    current = getattr(_local, "opener", None)
    if current is None or getattr(_local, "pid", None) != pid:
        if current is not None:
            current.close()
        current = HTTPSOpener()
        _local.opener, _local.pid = current, pid
    return current


def close():
    current = getattr(_local, "opener", None)
    if current is not None:
        current.close()
    _local.opener = None
