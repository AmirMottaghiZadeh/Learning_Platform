#!/usr/bin/env bash
# Container entrypoint for platforms that run the image directly (Runflare, plain
# `docker run`) with no separate release/pre-deploy hook. Applies migrations and
# the bundled ATC reference, then hands off to gunicorn.
#
# migrate / createcachetable / load_atc_reference are all idempotent, so running
# them on every boot is safe. Drug clinical data (import_openfda) is loaded
# out-of-band because it needs the multi-GB pipeline SQLite not shipped here.
#
# Every step is announced before it runs so a CrashLoopBackOff with a truncated
# log still shows exactly where it died.
set -uo pipefail

echo "[docker-start] $(date -Is) settings=${DJANGO_SETTINGS_MODULE:-unset} port=${PORT:-8000} cwd=$(pwd)"
python -c "import django, sys; print('[docker-start] django', django.get_version(), 'python', sys.version.split()[0])" || {
    echo "[docker-start] !!! python/django import failed — bad image"
    exit 1
}

run() {
    echo "[docker-start] >>> $*"
    if ! "$@"; then
        rc=$?
        echo "[docker-start] !!! FAILED (exit $rc): $*"
        exit "$rc"
    fi
}

run python manage.py migrate --no-input
# Creates the Postgres cache table(s) when CACHE_BACKEND is the DatabaseCache
# (the no-Redis deployment). No-op for a Redis cache.
run python manage.py createcachetable
run python manage.py load_atc_reference

echo "[docker-start] starting gunicorn on 0.0.0.0:${PORT:-8000}"
exec gunicorn config.wsgi:application \
    --config gunicorn.conf.py \
    --bind "0.0.0.0:${PORT:-8000}"
