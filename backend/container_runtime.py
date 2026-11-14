"""Supervise web and Celery processes after the single migration phase.

Tini in the image reaps orphaned descendants. A failed service stops the
container, so the platform can restart the entire group instead of leaving a
working HTTP endpoint with a dead search worker.
"""
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def commands(environ):
    concurrency = environ.get("AI_LAB_WORKER_CONCURRENCY", "1")
    if not re.fullmatch(r"[1-9][0-9]?", concurrency) or int(concurrency) > 32:
        raise ValueError("invalid AI_LAB_WORKER_CONCURRENCY")
    return [
        ("web", ["bash", str(Path(__file__).with_name("web-start.sh"))]),
        ("search-worker", ["celery", "-A", "config", "worker", "-Q", "ai_search",
                           "-c", concurrency, "--prefetch-multiplier", "1",
                           "--hostname", "search@%h", "--loglevel", "INFO"]),
        # Keep password-reset email and support deliveries off the long search
        # queue when switching the platform from eager to real Celery execution.
        ("platform-worker", ["celery", "-A", "config", "worker", "-Q", "default,events,maintenance",
                             "-c", "1", "--prefetch-multiplier", "1",
                             "--hostname", "platform@%h", "--loglevel", "INFO"]),
    ]


def stop_processes(children, timeout):
    # TERM the worker parent first: Celery performs a warm shutdown and waits
    # for its task children. Signalling the entire group here would kill them.
    for _, child in children:
        if child.poll() is None:
            try:
                child.terminate()
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + timeout
    try:
        for _, child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                pass
    finally:
        # Clean up descendants too, including those of a parent that crashed.
        for _, child in children:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for _, child in children:
            child.wait()


def supervise(process_commands, *, shutdown_seconds=60):
    children = []
    stopping = False

    def request_stop(signum, frame):
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        for name, command in process_commands:
            if stopping:
                return 0
            child = subprocess.Popen(command, start_new_session=True)
            children.append((name, child))
            print(f"[container-runtime] started {name} pid={child.pid}", flush=True)
        while not stopping:
            for name, child in children:
                code = child.poll()
                if code is not None:
                    print(f"[container-runtime] {name} exited code={code}; stopping container", flush=True)
                    return code if code > 0 else 1
            time.sleep(0.05)
        print("[container-runtime] shutdown requested", flush=True)
        return 0
    except OSError as exc:
        print(f"[container-runtime] process start failed: {type(exc).__name__}", flush=True)
        return 1
    finally:
        try:
            stop_processes(children, shutdown_seconds)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)


def main():
    try:
        timeout = int(os.environ.get("AI_LAB_WORKER_SHUTDOWN_SECONDS", "60"))
        if not 1 <= timeout <= 300:
            raise ValueError("invalid AI_LAB_WORKER_SHUTDOWN_SECONDS")
        process_commands = commands(os.environ)
    except ValueError:
        print("[container-runtime] invalid worker runtime configuration", flush=True)
        return 1
    return supervise(process_commands, shutdown_seconds=timeout)


if __name__ == "__main__":
    raise SystemExit(main())
