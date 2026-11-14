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

# Runflare can deploy this same image as a separate queue consumer. A worker
# never races the web/release service by applying migrations on its own boot.
case "${SERVICE_ROLE:-web}" in
    web) ;;
    ai-search-worker)
        concurrency="${AI_LAB_WORKER_CONCURRENCY:-2}"
        if ! [[ "$concurrency" =~ ^[1-9][0-9]?$ ]] || [ "$concurrency" -gt 32 ]; then
            echo "[docker-start] invalid AI_LAB_WORKER_CONCURRENCY"
            exit 1
        fi
        echo "[docker-start] starting dedicated ai_search worker; concurrency=$concurrency"
        exec celery -A config worker -Q ai_search -c "$concurrency" \
            --prefetch-multiplier 1 --loglevel INFO
        ;;
    *)
        echo "[docker-start] invalid SERVICE_ROLE"
        exit 1
        ;;
esac

run() {
    echo "[docker-start] >>> $*"
    # Capture the status directly: inside `if ! cmd; then`, $? is the negated
    # result (0), which made a failed step exit the container with success.
    "$@"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        echo "[docker-start] !!! FAILED (exit $rc): $*"
        exit "$rc"
    fi
}

run python manage.py migrate --no-input
if [ -n "${AI_LAB_FEEDBACK_DATABASE_URL:-}" ]; then
    run python manage.py migrate ai_feedback --database=ai_feedback --no-input
fi
if [ -n "${REFERENCE_SEARCH_DATABASE_URL:-}" ]; then
    run python manage.py migrate --database=reference_search --no-input
fi
# Existing MySQL mirrors need a title-only index before serving searches.
# No-op when UpToDate uses the read-only SQLite snapshot.
run python manage.py ensure_uptodate_search_index
# Creates the Postgres cache table(s) when CACHE_BACKEND is the DatabaseCache
# (the no-Redis deployment). No-op for a Redis cache.
run python manage.py createcachetable
run python manage.py load_atc_reference
# Starting content for the public site (menus, home blocks, pages); only fills what is empty.
run python manage.py seed_website
# Must run here, not at build time: production settings use WhiteNoise's
# ManifestStaticFilesStorage, so the staticfiles.json manifest has to be built
# under the production settings module (the image builds it under local, which
# has no manifest -> admin / browsable API / Swagger UI 500 without this).
run python manage.py collectstatic --no-input

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
