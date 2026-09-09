#!/usr/bin/env bash
# Release phase: runs once per deploy, after build, with the runtime environment
# available (DATABASE_URL, REDIS_URL / CELERY_BROKER_URL, a strong SECRET_KEY).
set -o errexit

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

python manage.py check --deploy
python manage.py migrate --no-input
python manage.py load_atc_reference

# Drug data is imported separately (import_openfda needs the ~2.3 GB pipeline
# SQLite, which is not shipped with the app). See the deployment notes.
