"""Check the actual Kombu Redis client path without opening a connection."""
from importlib.metadata import version
from types import SimpleNamespace

from kombu.transport.redis import Channel


def check_transport():
    # This is the same code path that raises VersionMismatch during startup.
    client_class = Channel._get_client(SimpleNamespace(global_keyprefix=""))
    client = client_class(host="127.0.0.1", port=6379, db=15,
                          socket_connect_timeout=1, socket_timeout=1)
    client.close()
    return {name: version(name) for name in ("redis", "celery", "kombu")}


if __name__ == "__main__":
    print("Redis transport client check passed:", check_transport())
