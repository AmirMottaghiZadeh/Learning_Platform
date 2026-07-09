# K_Game Frontend

Expo + React Native Web client for the K_Game reference implementation.

The frontend is a universal runtime surface:

- web application
- mobile-first browser experience
- future Android/iOS builds

## Run

```bash
npm ci
cp .env.example .env
npm run web -- --port 8081
```

Default API base:

```text
http://127.0.0.1:8000/api/v1
```

Override with:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## GitHub Pages Deployment

Production frontend URL:

```text
https://AmirMottaghiZadeh.github.io/Learning_Platform/
```

Production API base:

```text
https://amirmtz.runflare.run/api/v1
```

Deployment is handled by `.github/workflows/frontend-pages.yml` on every push to `main`.

The workflow:

- uses Node 20
- runs `npm ci` inside `frontend`
- builds with `npm run build:web`
- deploys `frontend/dist` to GitHub Pages

Required build-time environment variables:

```text
EXPO_BASE_URL=/Learning_Platform
EXPO_PUBLIC_API_BASE_URL=https://amirmtz.runflare.run/api/v1
```

`EXPO_BASE_URL` is used only for hosted builds so Expo emits asset paths under `/Learning_Platform/`.
Local development does not need it and still runs at the root path:

```bash
npm run web -- --port 8081
```

For client-side routing fallback on GitHub Pages, the workflow copies `dist/index.html` to `dist/404.html` and writes `dist/.nojekyll`.

## Architecture Rules

- Frontend renders platform state.
- Backend owns correctness, scoring, review scheduling, mastery, progress, and league ranking.
- API responses are typed in `src/types/api.ts`.
- API calls are centralized in `src/api/platform.ts`.
- Safe `GET` requests use limited retry behavior in `src/api/client.ts`.
- Reusable UI lives in `src/components/ui.tsx`.
- Design tokens live in `src/design/tokens.ts`.
- PWA assets and HTML shell live in `public/` and are copied into `dist/` during `npm run build:web`.
- Onboarding and planning are product-layer UX flows; they do not change platform learning rules.

## Screens

- Dashboard
- Onboarding
- Quiz
- Flashcards
- Planning
- Mistakes
- League
- Statistics
- Profile

## UX Direction

- Mobile-first app shell with a 430px maximum content width.
- Dashboard answers “what should I do today?” before listing secondary content.
- Learning loop is visible as learn, review, relearn, and check.
- Onboarding uses short story steps, progress, skip, and fast text reveal.
- Install guidance and PWA metadata support standalone web-app usage.

## Phase 7 Notes

- Flashcards consume the full backend deck contract and deck summary.
- League consumes the unified backend league summary.
- Statistics shows daily activity, topic progress, and weak-topic signals.
- The app remains mobile-first and runs on React Native Web.
