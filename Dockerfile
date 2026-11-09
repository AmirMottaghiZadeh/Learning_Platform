FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    ALLOWED_HOSTS=localhost \
    SECURE_SSL_REDIRECT=False \
    SECURE_HSTS_SECONDS=0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client libexpat1 libxrender1 libxext6 libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Fail the build if the RDKit drawing runtime cannot load on the slim image.
RUN python -c "from rdkit.Chem.Draw import rdMolDraw2D; rdMolDraw2D.MolDraw2DSVG(640, 360)"

COPY backend/ .

# The executable bit can be lost depending on how the platform fetches the repo
# (a zip archive drops Unix modes); set it here and invoke via bash so the entry
# point runs regardless.
RUN chmod +x docker-start.sh release.sh build.sh

RUN DJANGO_SETTINGS_MODULE=config.settings.local python manage.py collectstatic --no-input

EXPOSE 8000

# Runs migrations + ATC reference (both idempotent) on boot, then gunicorn.
CMD ["bash", "docker-start.sh"]
