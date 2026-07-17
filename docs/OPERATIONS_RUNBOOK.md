# Operations Runbook

This runbook follows Volume VIII of the Learning Platform Architecture & Engineering Book.

## Environments

- Local: developer machine with local PostgreSQL.
- Docker: production-like local stack with PostgreSQL.
- Staging: production-like validation environment.
- Production: live user environment.

Secrets must be configured through environment variables, not committed.

## Required Backend Environment

```bash
DJANGO_SETTINGS_MODULE=config.settings.production
ENVIRONMENT=production
SECRET_KEY=<strong-secret>
DATABASE_URL=<postgres-url>
ALLOWED_HOSTS=<api-hosts>
CSRF_TRUSTED_ORIGINS=https://<frontend-host>,https://<api-host>
CORS_ALLOWED_ORIGINS=https://<frontend-host>
AI_DATA_PIPELINE_PROVIDER=rules
LOG_FORMAT=json
PASSWORD_RESET_FRONTEND_URL=https://<frontend-host>/
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-secret>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=<verified-sender-email>
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://<redis-host>:6379/1
```

## Authentication security

- Login, registration, password-reset request, and password-reset confirmation are rate-limited by DRF. Configure the `DRF_*_THROTTLE_RATE` variables for expected traffic.
- In production, use a shared Redis cache. `LocMemCache` limits one application worker only and is not sufficient when Gunicorn runs multiple workers or instances.
- Password-reset emails use Django's signed, time-limited reset token. Configure the SMTP variables above and a verified `DEFAULT_FROM_EMAIL`; without them users cannot receive reset emails.
- API bearer tokens expire after `AUTH_TOKEN_TTL_HOURS` (24 hours by default). Changing a password invalidates all existing API tokens.
- The Expo web client currently persists its DRF token through AsyncStorage, which maps to browser storage on web. A successful XSS attack could read it. Keep the token lifetime short, use HTTPS, maintain a strict Content Security Policy at the frontend host, and plan a future same-site httpOnly-cookie session architecture before treating the browser client as high-assurance.

For local production-like Docker, use:

```bash
rtk docker compose up --build
```

Backend: `http://127.0.0.1:8000`  
Frontend web: `http://127.0.0.1:8081`

## Health Checks

- Liveness: `GET /api/v1/live/`
- Readiness: `GET /api/v1/ready/`
- Full health: `GET /api/v1/health/`

The readiness/full health checks verify database connectivity and return release metadata.

## CI Checks

GitHub Actions runs:

- Backend dependency install
- `manage.py check`
- `manage.py check --deploy --settings=config.settings.production`
- migration drift check
- database backup dry-run
- backend tests
- frontend typecheck
- frontend web build

## Deployment

Render deployment is described in `backend/render.yaml`.

Before production deployment:

```bash
cd backend
rtk .venv/bin/python manage.py check --deploy --settings=config.settings.production
rtk .venv/bin/python manage.py makemigrations --check --dry-run
rtk .venv/bin/python manage.py test
```

Then verify:

```bash
rtk curl https://<api-host>/api/v1/health/
```

## Backups

Create a backup before applying production data changes:

```bash
cd backend
rtk .venv/bin/python manage.py backup_database --name pre-release
```

For PostgreSQL, `pg_dump` must be installed in the runtime environment.

Recommended policy:

- Daily automated backups.
- Manual backup before migrations or data-quality apply operations.
- Retain at least 7 daily and 4 weekly backups.
- Test restore at least monthly.

## Restore

PostgreSQL restore:

```bash
pg_restore --clean --if-exists --dbname "$DATABASE_URL" backups/<backup>.dump
```

Always restore into staging first before production.

## Logging

Production logs are JSON-formatted and include:

- timestamp
- level
- logger
- request_id
- event
- module

Every HTTP response includes `X-Request-ID`.

## Release Checklist

- CI green.
- Migration check clean.
- Production deploy check reviewed.
- Backup created.
- Health endpoint green after deploy.
- Admin access reviewed.
- Rollback plan identified.
- Data Quality Center suggestions are not applied without approval.

## Rollback

Application rollback:

1. Redeploy the previous known-good version.
2. Verify `/api/v1/health/`.
3. Check error logs and critical flows.

Database rollback:

1. Prefer forward fix when possible.
2. If restore is required, restore into staging first.
3. Confirm owner approval before production restore.

## Incident Response

1. Detect and record the incident time.
2. Assign an owner.
3. Check health endpoint, logs, database availability and recent deploys.
4. Mitigate the active issue.
5. Communicate user impact.
6. Write follow-up actions.
