#!/usr/bin/env bash
# Container entrypoint for platforms that run the image directly (Runflare, plain
# `docker run`) and have no separate release/pre-deploy hook. Applies migrations
# and the bundled ATC reference, then hands off to gunicorn.
#
# migrate and load_atc_reference are both idempotent, so running them on every
# boot is safe. Drug clinical data (import_openfda) is loaded out-of-band because
# it needs the multi-GB pipeline SQLite that is not shipped in the image.
set -o errexit

python manage.py migrate --no-input
# Creates the Postgres cache table(s) when CACHE_BACKEND is the DatabaseCache
# (the no-Redis deployment). No-op for a Redis cache. Safe to run every boot.
python manage.py createcachetable
python manage.py load_atc_reference

exec gunicorn config.wsgi:application --config gunicorn.conf.py
