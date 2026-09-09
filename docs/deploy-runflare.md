# Deploying the backend on Runflare (single container, no Redis)

Runflare runs the Docker image directly (no separate release/pre-deploy hook)
and the free plan allows only **one app + one database** — no room for a
managed Redis. This is the supported "small deployment" shape:

- **Migrations + ATC reference** run on container boot via `backend/docker-start.sh`
  (both idempotent). The image `CMD` points at that script.
- **Cache / throttling** use a Postgres-backed table cache
  (`django.core.cache.backends.db.DatabaseCache`) instead of Redis. It is a real
  cross-process shared cache, so login throttling still holds across Gunicorn
  workers. `docker-start.sh` runs `createcachetable` each boot.
- **Background jobs** run synchronously inside the web request
  (`CELERY_RUN_TASKS_IN_REQUEST=True`). No Celery worker, no broker. The only
  in-request task today is the password-reset email; with
  `ASYNC_EMAIL_ENABLED=False` it is sent inline anyway.

If a managed Redis ever becomes available, drop `CELERY_RUN_TASKS_IN_REQUEST`,
`CACHE_BACKEND`, `CACHE_LOCATION` and set `REDIS_URL` (+ `CELERY_BROKER_URL`)
instead, then run a `worker` process — that is the `render.yaml` shape.

## Environment variables

Set these on the Runflare app. Replace `<VERCEL_URL>` with the real frontend
origin (scheme + host only, **no path, no trailing slash**), e.g.
`https://pharmexa.vercel.app`.

```bash
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<a random string of 50+ chars, 12+ distinct, no spaces, not all digits>
DEBUG=False
ALLOWED_HOSTS=amirmtz.runflare.run,127.0.0.1,localhost

# Postgres that Runflare provisioned — keep the internal service host as-is
DATABASE_URL=postgresql://postgres:<pw>@database-egt-service:5432/databasepyz_db

# Cache without Redis: a Postgres table cache
CACHE_BACKEND=django.core.cache.backends.db.DatabaseCache
CACHE_LOCATION=pharmexa_cache

# Background jobs without a broker: run them inline
CELERY_RUN_TASKS_IN_REQUEST=True
ASYNC_EMAIL_ENABLED=False

# Cross-origin: the Vercel frontend
CORS_ALLOWED_ORIGINS=<VERCEL_URL>
CORS_ALLOW_CREDENTIALS=True
CSRF_TRUSTED_ORIGINS=https://amirmtz.runflare.run,<VERCEL_URL>
PASSWORD_RESET_FRONTEND_URL=<VERCEL_URL>/reset-password
```

Do **not** set: `CELERY_TASK_ALWAYS_EAGER` (the flag above handles it),
`REDIS_URL`, `CELERY_BROKER_URL`, `LEARNING_PRODUCT_ADAPTER`,
`AI_DATA_PIPELINE_PROVIDER` (the last two are from the pre-rewrite codebase).

`SECURE_SSL_REDIRECT` / `SECURE_HSTS_SECONDS` default to off in the image to
avoid a redirect loop on the first deploy. Once HTTPS is confirmed working
behind Runflare's proxy you can set `SECURE_SSL_REDIRECT=True`.

Health-check path (if Runflare asks for one): `/api/v1/health/`.

## Loading the drug data

Migrations create the `drugs_*` tables empty. The clinical profiles live in the
multi-GB pipeline SQLite on the developer laptop, not in the image. Load them
once, from the laptop, against Runflare's **external** Postgres connection
string (from the Postgres service dashboard):

```bash
cd backend
DATABASE_URL="postgresql://postgres:<pw>@<external-host>:<port>/databasepyz_db?sslmode=require" \
DJANGO_SETTINGS_MODULE=config.settings.local \
python manage.py import_openfda --source /home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db
```

Expected rows: `drugs_ingredient` 1794, `drugs_atccode` 542,
`drugs_atccategory` 98, `drugs_ingredient_atc_codes` 1918,
`drugs_ingredientprofilesection` 21528.

Alternative (no laptop Django run): `pg_dump --data-only` those five tables from
the local `pharmexa_dev` DB and pipe into the external `psql` prefixed with
`SET session_replication_role = replica;` to defer FK checks.

## Verify

```bash
curl -i https://amirmtz.runflare.run/api/v1/health/
curl -i https://amirmtz.runflare.run/api/v1/ready/        # 200 => DB + cache OK
curl    "https://amirmtz.runflare.run/api/v1/drugs/?search=losartan"
```

Create the admin user from the Runflare console:

```bash
python manage.py createsuperuser
```
