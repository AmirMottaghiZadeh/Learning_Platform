#!/usr/bin/env bash
# Release phase: runs once per deploy, after build, with the runtime environment
# available (DATABASE_URL, REDIS_URL / CELERY_BROKER_URL, a strong SECRET_KEY).
set -o errexit

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

python manage.py check --deploy
python manage.py migrate --no-input
python manage.py createcachetable
python manage.py load_atc_reference

# No-op unless DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD are set — for hosts
# with no shell/one-off-job access (Render's free plan, same issue we hit on
# Runflare) to still get an admin account without one.
python manage.py bootstrap_superuser

# Drug data is imported separately (import_openfda needs the ~2.3 GB pipeline
# SQLite, which is not shipped with the app). See the deployment notes.
