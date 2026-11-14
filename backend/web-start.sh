#!/usr/bin/env bash
# Web process only: migrations belong to docker-start.sh.
set -uo pipefail

if [ "${APP_SERVER:-asgi}" = "asgi" ]; then
    echo "[docker-start] starting ASGI on 0.0.0.0:${PORT:-8000}"
    exec uvicorn config.asgi:create_application --factory \
        --host 0.0.0.0 --port "${PORT:-8000}" \
        --workers "${WEB_CONCURRENCY:-2}" --no-access-log --timeout-keep-alive 5
fi
echo "[docker-start] starting gunicorn on 0.0.0.0:${PORT:-8000}"
exec gunicorn config.wsgi:application \
    --config gunicorn.conf.py \
    --bind "0.0.0.0:${PORT:-8000}"
