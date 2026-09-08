# Pharmexa API contract — v1

Base path `/api/v1/`. Every route also has an unversioned `/api/…` alias.
Auth: `Authorization: Bearer <access_token>` (opaque `UserSession` token; refresh
via `POST /auth/refresh/`). All errors use the platform envelope
`{ "code", "message", "details" }`.

Status key: **✅ built** (Phase 2) · **🔜 Phase 3** (shape frozen here, logic + models land with the stateful apps).

Bilingual text fields come in pairs (`*_fa` / `*_en`); the client picks by the
active language. Persian is the default.

---

## Auth & onboarding

| Method | Path | Status | Notes |
|---|---|---|---|
| POST | `/auth/register/` | ✅ | body `{name, email, password, password_confirm}` → `AuthTokenResponse` |
| POST | `/auth/login/` | ✅ | `{username, password, device_name?}` → `AuthTokenResponse` |
| POST | `/auth/refresh/` | ✅ | `{refresh_token}` → `AuthTokenResponse` (refresh rotates) |
| POST | `/auth/logout/` · `/auth/logout-all/` | ✅ | revoke current / all sessions |
| GET | `/auth/me/` | ✅ | → `User` (incl. `profile`) |
| PATCH | `/auth/me/` | ✅ | body = partial `LearnerProfile` (e.g. `{display_name}`) → `User` |
| POST | `/auth/onboarding/` | ✅ | `{study_field, study_goal, study_level, display_name?, language?}` → `User`; sets `profile.onboarded_at` |
| GET | `/auth/sessions/` · POST `/auth/sessions/{id}/revoke/` | ✅ | device list / revoke |
| POST | `/auth/step-up/` | ✅ | re-verify password for sensitive actions |
| GET/POST | `/auth/password-reset/` · `/auth/password-reset/confirm/` | ✅ | |
| GET | `/auth/roles/` · `/auth/role-assignments/` · `/auth/security-events/` | ✅ | RBAC / audit (staff) |

```jsonc
// User
{
  "id": 1, "username": "sara", "email": "sara@example.com",
  "first_name": "Sara", "last_name": "Karimi",
  "roles": ["learner"],
  "profile": {                     // LearnerProfile
    "display_name": "Sara Karimi",
    "study_field": "pharmacy",     // "" | pharmacy | medicine | nursing
    "study_goal": "residency",     // "" | residency | final | clinical
    "study_level": "advanced",     // "" | beginner | intermediate | advanced
    "language": "fa",
    "onboarded_at": "2026-09-09T…" | null,
    "is_onboarded": true
  }
}
// AuthTokenResponse
{ "user": {…User}, "access_token": "phx_access_…", "refresh_token": "phx_refresh_…",
  "token_type": "Bearer", "access_expires_at": "…", "refresh_expires_at": "…", "session_id": "uuid" }
```

Design mapping — onboarding screen: `OB_FIELDS`→`study_field`, `OB_GOALS`→`study_goal`,
`OB_LEVELS`→`study_level`. After step 3 the client `POST /auth/onboarding/` then
routes to dashboard.

---

## Drug knowledge (read-only, no per-user state)

| Method | Path | Status |
|---|---|---|
| GET | `/drugs/` | ✅ |
| GET | `/drugs/{slug}/` | ✅ |
| GET | `/atc/` | ✅ |

### `GET /drugs/` — paginated list

Query: `search` (name prefix or exact RXCUI), `atc` (ATC code prefix, e.g. `C09`),
`page`. Response: standard pagination envelope, `results[]` of:

```jsonc
{
  "rxcui": "52175", "name": "losartan", "slug": "losartan-52175",
  "n_products": 7, "n_source_records": 206,
  "pharm_classes": ["Angiotensin 2 Receptor Blocker"],
  "atc_codes": [{ "code": "C09CA", "name": "Angiotensin II receptor blockers (ARBs), plain", "level": 4 }]
}
```

### `GET /drugs/{slug}/` — ingredient detail

List fields **plus**:

```jsonc
{
  "sections": [                    // every clinical field present, model order
    { "field": "clinical_pharmacology", "label": "Clinical pharmacology",
      "has_content": true, "has_summary": true, "n_contributing_products": 5,
      "summary_fa": "…", "summary_en": "…", "raw_text": "…full label text…" }
    // … up to 12: indications_and_usage, dosage_and_administration,
    //   dosage_forms_and_strengths, contraindications, do_not_use, boxed_warning,
    //   warnings, adverse_reactions, drug_interactions, pregnancy, abuse
  ],
  "lesson_sections": [             // the design's lesson-card view; summary-only
    { "key": "mechanism", "field": "clinical_pharmacology",
      "title_fa": "مکانیسم", "title_en": "Mechanism",
      "tone": "info",             // info | deny | boxed | caution | special
      "text_fa": "…", "text_en": "…", "has_summary": true }
    // keys, in order: mechanism, indication, dose, forms, contraindications,
    //   do_not_use, boxed_warning, warning, side, interactions, pregnancy, abuse
    // a key is omitted when that field has no fa/en summary yet
  ]
}
```

`lesson_sections` is exactly what the design's lesson-detail screen renders
(`FIELD_MAP` + `LESSON_EXTRA`, `tone` drives the section colour).

### `GET /atc/` — ATC codes in the dataset

Query: `prefix`. Not paginated. `[{ "code", "name", "level", "ingredient_count" }]`.
Currently every code is level 4 (5 chars). The L1/L2 grouping + Persian category
names for the lessons taxonomy are built in Phase 3.

---

## 🔜 Phase 3 — stateful screens (shape frozen, models pending)

These need per-user progress / session models (`apps.lessons`, `apps.quiz`,
`apps.flashcards`, a `me` progress store). The response shapes below are the
contract Phase 3 implements behind the same routes.

### Lessons

- **GET `/lessons/groups/`** — the ATC study tree with progress.
  ```jsonc
  [{ "code": "N", "name_fa": "سیستم عصبی", "name_en": "Nervous system",
     "subgroups": [{ "code": "N02", "name_fa": "مسکن‌ها", "name_en": "Analgesics",
                     "total": 6, "done": 5 }] }]
  ```
- **GET `/lessons/chapters/{atc_code}/`** — one chapter (ATC subgroup).
  ```jsonc
  { "code": "N02", "name_fa": "…", "name_en": "…",
    "drugs": [{ …IngredientDetail with lesson_sections… }],
    "progress": { "read_drug_slugs": ["…"], "scroll_pct": 0 } }
  ```
- **POST `/lessons/chapters/{atc_code}/progress/`** — `{drug_slug, scroll_pct}`.

### Dashboard — GET `/me/dashboard/`

```jsonc
{
  "greeting_name": "سارا",
  "streak_days": 4, "xp": 1280,
  "next_chapter": { "code": "N05", "name_fa": "…", "name_en": "…", "group_name_fa": "…" },
  "focus_session": {
    "rows": [
      { "kind": "leitner", "title_fa": "…", "sub_fa": "…", "minutes": 4, "count": 10 },
      { "kind": "mistake",  "title_fa": "…", "sub_fa": "…", "minutes": 3, "mistake_id": 2 },
      { "kind": "lesson",   "title_fa": "…", "sub_fa": "…", "minutes": 2, "atc_code": "N05" }
    ],
    "total_minutes": 9
  }
}
```

### Mistakes — GET `/me/mistakes/` · POST `/me/mistakes/{id}/resolve/` · POST `/me/mistakes/restore/`

```jsonc
[{ "id": 1, "topic_fa": "عوارض جانبی", "topic_en": "Side effects",
   "count": 4, "detail_fa": "…", "detail_en": "…", "resolved": false }]
```

### Statistics — GET `/me/statistics/`

```jsonc
{ "week_bars": [40,65,50,80,45,90,70],       // minutes/day, Sat→Fri
  "accuracy_pct": 78, "quizzes": 12, "reviews": 340, "minutes": 620,
  "mastery_pct": 61 }
```

### Planning — GET `/me/plan/` · PUT `/me/plan/`

```jsonc
{ "days": [true,false,true,true,false,true,false], "reminders_enabled": true }
// day index 0..6 = Sat..Fri (DAY_LABELS_FULL)
```

### Profile — GET `/me/profile/` (or reuse `/auth/me/`) · PATCH settings

```jsonc
{ "display_name": "…", "email": "…",
  "stats": { "accuracy_pct": 78, "quizzes": 12 },
  "settings": { "notifications": true, "language": "fa" } }
```

### Flashcards — **locked** (feature flag off; routes 503 until Phase 3 opens them)

- GET `/flashcards/` — due cards `[{ id, front_fa, front_en, back_fa, back_en, box }]`
- GET `/flashcards/boxes/` — Leitner box summary
- POST `/flashcards/{id}/review/` — `{rating: "easy"|"hard"}` → next due
- POST `/flashcards/seed/` — build the deck from lesson drugs

### Quiz — **locked**

- POST `/quiz/start/` — `{category, count}` → `{session_id, questions:[{id, prompt_fa, prompt_en, options_fa[], options_en[]}]}`
- POST `/quiz/{session_id}/answer/` — `{question_id, selected_index, client_answered_at}` → `{correct, correct_index}` (server scores)
- POST `/quiz/{session_id}/finish/` → `{score, total, mistakes_added}`
- Categories: `general | antibiotics | cardio | interactions`; counts `5|10|15|20`.

### uptodate — **Phase 6** (separate data source, `/home/amir/Documents/UpToDate/`)

- GET `/uptodate/topics/?search=` — `[{ id, title_fa, title_en, section_fa, section_en, updated_at }]`
- GET `/uptodate/topics/{id}/` — rendered article

---

## Notes for Phase 3

- The design's `ATC_GROUPS` names ("سیستم عصبی", "مسکن‌ها") need an ATC L1/L2
  reference with fa/en names — not in `pipeline_v2.db`. Bundle a small curated
  table (~14 L1 + ~84 L2 codes that appear in our data).
- Quiz questions are generated from `IngredientProfileSection` warnings/limits;
  the server owns correctness, scoring, timer and mistake attribution (the
  client only sends the selected index + client timestamp).
- `xp` / `streak` live on a per-user progress record updated after each quiz and
  review; `league` is intentionally dropped.
