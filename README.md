# Pharmexa

A bilingual (فارسی / English) drug-knowledge learning app: lessons built from
real OpenFDA drug data, spaced-repetition flashcards, quizzes, a personal
progress dashboard, and a read-only UpToDate clinical reference.

- **Backend** — Django REST, PostgreSQL, opaque-session auth.
- **Frontend** — Expo (React Native) + `react-native-web`; one codebase for
  iOS, Android and web.
- **Design system** — `frontend/src/theme/tokens.ts` (palette, spacing, radii,
  shadows) and `frontend/src/i18n/strings.ts` (UI copy, fa/en); RTL and
  light/dark throughout.

> Educational software, not clinical decision support. Generated learning
> content and drug summaries need review by qualified people before production
> use.

Progress and the full plan: **[PHASES.md](PHASES.md)**.
API shapes: **[docs/api-contract.md](docs/api-contract.md)**.

---

## Architecture

The backend owns everything that must not be client-trusted: auth, answer
correctness, scoring, streak/XP, review scheduling, mistake attribution.

### Backend apps (`backend/apps/`)

| app | role |
|---|---|
| `accounts` | opaque `UserSession` bearer tokens (rotation + instant revoke), RBAC, security audit, step-up, password reset |
| `core` | health/live/ready, request-id logging, exceptions envelope, throttling, a thin Celery layer for password-reset email |
| `drugs` | `Ingredient` / `IngredientProfileSection` / `AtcCode` / `AtcCategory`; `import_openfda` loads the OpenFDA pipeline SQLite; `load_atc_reference` seeds the bilingual ATC tree |
| `lessons` | ATC taxonomy → chapters (drug + section content), per-chapter progress |
| `progress` | `LearnerProgress` (xp, streak, totals), `DailyStudy`, `Mistake`, `StudyPlan`; the `/me/*` endpoints |
| `flashcards` | Leitner cards; `build_flashcards` extracts each drug's card facts (5 sections) — **locked** behind `FLASHCARDS_API_ENABLED` |
| `quiz` | server-scored quiz from a question bank built off the card facts (`build_question_bank`), feeds progress + mistakes — **locked** behind `QUIZ_API_ENABLED` |
| `uptodate` | read-only search + article API over the bundled UpToDate SQLite snapshot (no models); 503 when the snapshot is absent |
| `data_quality_center` | staff console at `/ops/data-quality/` to edit section summaries, with superuser approval and an audit trail (off with `DATA_QUALITY_CENTER_ENABLED=False`) |

### Frontend (`frontend/src/`)

`theme/` design tokens + provider · `i18n/` fa/en strings + RTL provider ·
`api/` axios client with a `UserSession` refresh interceptor + typed endpoints ·
`store/` zustand (`auth`, `nav` — an app-managed state machine, not a router) ·
`components/` shared primitives + `AppShell` + `BottomNav` · `screens/` one file
per screen · `navigation/Navigator.tsx` gates on auth + onboarding.

---

## Running it

### Docker (backend + db + redis + web frontend)

```bash
export SECRET_KEY="a strong 50+ character secret"
docker compose up --build
# backend  http://localhost:8000   (API docs at /api/v1/docs/)
# frontend http://localhost:8081
```

### Backend, locally

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point DATABASE_URL at your Postgres
python manage.py migrate
python manage.py load_atc_reference
python manage.py import_openfda            # needs the OpenFDA pipeline SQLite
python manage.py import_calculators_db --source calculators.db   # from export_reference_db
python manage.py import_guidelines_db  --source guidelines.db
python manage.py import_diseases_db    --source diseases.db
python manage.py build_flashcards          # card facts, from the profile summaries
python manage.py build_question_bank       # quiz bank, from the card facts
python manage.py runserver
```

`import_openfda` reads `UPTODATE`-style upstreams read-only; re-run any time
(idempotent), or `--only-summaries` to sync just the fa/en summaries.

### Frontend, locally

```bash
cd frontend
npm install
npm run web            # or: npm run ios / npm run android / npm start
```

Set `EXPO_PUBLIC_API_BASE_URL` (see `.env.example`); on a device use your
machine's LAN IP, not `127.0.0.1`.

To preview the locked features: run the backend with
`QUIZ_API_ENABLED=True FLASHCARDS_API_ENABLED=True`.

The UpToDate reference needs the snapshot directory (`UPTODATE_DB_DIR`,
default `/home/amir/Documents/UpToDate`); without it those endpoints answer 503
and the screen shows a "coming soon" state.

---

## Tests

```bash
cd backend && python manage.py test          # Django test runner
cd frontend && npm run typecheck             # tsc --noEmit
cd frontend && npm run build:web             # expo export (bundles the app)
```

CI (`.github/workflows/ci.yml`) runs the backend suite + deploy checks and the
frontend typecheck + web build on every push and PR.

---

## Deploy

- **Backend** — `backend/render.yaml` (Render blueprint); `config.settings.production`
  enforces a real broker + cache and a strong secret.
- **Web frontend** — `frontend/Dockerfile` (nginx) or GitHub Pages via
  `.github/workflows/frontend-pages.yml` (manual dispatch).
- **Native** — `frontend/eas.json`; `eas build --platform ios|android`.
