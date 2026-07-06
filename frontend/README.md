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

## Architecture Rules

- Frontend renders platform state.
- Backend owns correctness, scoring, review scheduling, mastery, progress, and league ranking.
- API responses are typed in `src/types/api.ts`.
- API calls are centralized in `src/api/platform.ts`.
- Safe `GET` requests use limited retry behavior in `src/api/client.ts`.
- Reusable UI lives in `src/components/ui.tsx`.
- Design tokens live in `src/design/tokens.ts`.

## Screens

- Dashboard
- Quiz
- Flashcards
- Mistakes
- League
- Statistics
- Profile

## Phase 7 Notes

- Flashcards consume the full backend deck contract and deck summary.
- League consumes the unified backend league summary.
- Statistics shows daily activity, topic progress, and weak-topic signals.
- The app remains mobile-first and runs on React Native Web.

