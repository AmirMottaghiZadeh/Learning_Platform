#!/usr/bin/env bash
# Build phase: only steps that need no runtime env (DB, Redis, real SECRET_KEY).
# Migrations and the production --deploy check run in release.sh instead, where
# the platform has injected the runtime environment.
set -o errexit

pip install -r requirements.txt

# collectstatic needs no DB/broker; run it under local settings so the
# production security validators don't fire during the build.
DJANGO_SETTINGS_MODULE=config.settings.local python manage.py collectstatic --no-input
