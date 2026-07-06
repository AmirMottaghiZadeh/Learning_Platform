# Learning Platform / K_Game

Reusable learning-platform architecture with a Django REST backend, a K_Game reference implementation, and an Expo + React Native Web frontend.

## Repository Layout

- `backend/`: Django backend, REST API, quiz/game/flashcard/league modules, drug data layer, and AI data pipeline.
- `frontend/`: Expo + React Native Web client.
- `Learning_Platform_Architecture_Engineering_Book_Final/`: architecture and engineering book for the platform.
- `README_MIGRATION.md`: migration and architecture notes.

## Safety Notes

The repository is prepared for a private GitHub repo.

Do not commit:

- `backend/.env`
- `backend/db.sqlite3`
- `backend/.venv/`
- `frontend/node_modules/`
- generated exports/backups
- local editor/runtime files

The source of truth for local configuration is `.env.example` files.

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py import_drugs
python manage.py sync_learning_sources
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

With the local wrapper used in this workspace:

```bash
rtk .venv/bin/python manage.py check
rtk .venv/bin/python manage.py test
```

## Frontend Setup

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

Type check:

```bash
npm run typecheck
```

## AI Data Pipeline

The AI data pipeline is safe-by-default:

- local `rules` provider is active
- `openai` and `ollama` providers are placeholders only
- suggestions are saved as pending review items
- original drug records are not modified until approved suggestions are applied through the safe apply command
- day-to-day review happens in the dedicated internal **Data Quality Center** at `/data-quality/`
- Django Admin remains available for developers, but it is no longer the primary review interface

Useful commands:

```bash
cd backend
python manage.py ai_health_check
python manage.py ai_generate_suggestions --provider rules --limit 500 --include-normalization --include-terminology --include-duplicates --include-medical-validation --batch-name "Initial local cleanup review"
python manage.py ai_generate_report --batch-id 1
```

Apply approved suggestions only after manual review:

```bash
python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

Reference docs:

- `backend/apps/data_quality_center/README.md`
- `backend/apps/ai_data_pipeline/README.md`

## GitHub Private Repo Setup

See `docs/GITHUB_PRIVATE_SETUP.md`.
