# Repository Guidelines

## Project Structure & Module Organization

- `backend/` holds Django code, including `manage.py`, `config/` settings, and domain apps in `backend/apps/`.
- `backend/apps/*/tests.py` contains backend tests colocated with Django apps.
- `frontend/` holds the Expo app; main entry points are `frontend/App.tsx` and `frontend/src/`.
- `frontend/src/api/`, `components/`, `screens/`, `store/`, `types/`, and `design/` separate client calls, UI, views, state, types, and styling tokens.
- `docs/` and `Learning_Platform_Architecture_Engineering_Book_Final/` contain operations and architecture documentation.

## Build, Test, and Development Commands

- `docker compose up --build` starts the full stack locally.
- `cd backend && pip install -r requirements.txt` installs backend dependencies.
- `cd backend && python manage.py migrate` applies database migrations.
- `cd backend && python manage.py runserver 127.0.0.1:8000` runs the Django API locally.
- `cd backend && python manage.py test` runs the backend test suite.
- `cd frontend && npm ci` installs frontend dependencies from `package-lock.json`.
- `cd frontend && npm run web -- --port 8081` starts the Expo web dev server.
- `cd frontend && npm run typecheck` validates TypeScript.
- `cd frontend && npm run build:web` creates a static web export.

## Coding Style & Naming Conventions

Follow `.editorconfig`: UTF-8, LF endings, final newline, trimmed trailing whitespace, and spaces only. Use 4-space indentation by default and 2 spaces for `js`, `ts`, `tsx`, `json`, `yml`, and `yaml`.

Use `snake_case` for Python functions/modules, `PascalCase` for Django classes and React components, and descriptive TypeScript types such as `QuizSummary`. Keep backend business logic in `services.py`/`selectors.py` when present, and keep frontend API contracts in `frontend/src/types/` or `frontend/src/api/`.

## Testing Guidelines

Backend tests use Django’s test runner and live in `backend/apps/*/tests.py`. Name test methods with `test_...` and cover services, selectors, serializers, and API views when behavior changes.

The frontend currently relies on TypeScript and build checks; run `npm run typecheck` and `npm run build:web` for UI changes.

## Commit & Pull Request Guidelines

Git history favors short, imperative commit messages such as `Add GitHub Pages frontend deployment` or `Fix versioned OpenAPI schema generation`. Keep commits focused and avoid mixing unrelated backend, frontend, and documentation changes.

PRs should include a concise summary, testing performed, linked issues when applicable, and screenshots or recordings for visible UI changes.

## Security & Configuration Tips

Use `.env.example` files as templates and do not commit secrets, local databases, virtual environments, generated exports, `.expo/`, or build output. Prefer settings in `backend/config/settings/` and deployment notes in `docs/`.
