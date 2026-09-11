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

## Lessons — ✅ built (Phase 3a)

A *chapter* is an ATC L2 subgroup and its ingredients — unchanged, still keyed
and progress-tracked by the real ATC code. The *group* above it is a curated
clinical **study topic** (`apps/lessons/data/study_topics.py`), not the raw
ATC L1 anatomical parent: ATC is a mechanism/chemical classification (built
for WHO drug-utilisation stats), so e.g. beta blockers, thiazides, ACE
inhibitors/ARBs and calcium-channel blockers — all first-line
antihypertensives — sit in five unrelated-looking ATC L2 codes. The topic
table regroups existing, unmodified L2 codes by indication/organ system
instead, and a code can legitimately appear under more than one topic (beta
blockers are first-line for hypertension, heart failure, angina AND
arrhythmia alike) — each appearance is the same chapter, same drug list, same
progress record. A populated L2 code the table doesn't cover yet (e.g. a
freshly-imported ATC class) falls back to a group named after its true ATC
L1, so nothing silently disappears; `StudyTopicsCoverageTests` normally keeps
that fallback unreachable for the bundled reference data. An L2 subgroup is
only listed once at least one imported ingredient falls under it.

### `GET /lessons/groups/` — the study tree with progress

```jsonc
[{ "code": "cv-htn", "name_fa": "فشار خون بالا", "name_en": "Hypertension",
   "subgroups": [{ "code": "C07", "name_fa": "مسدودکننده‌های بتا",
                   "name_en": "Beta blocking agents",
                   "total": 16,          // ingredients under C07*
                   "done": 1 }] },       // of those, ones the learner has opened
 { "code": "cv-arrhythmia", "name_fa": "آریتمی قلبی", "name_en": "Cardiac arrhythmia",
   "subgroups": [{ "code": "C07", "…": "…" }] }]   // same C07 chapter, second topic
```

### `GET /lessons/chapters/{atc_code}/` — one chapter (ATC L2 subgroup)

`atc_code` is case-insensitive. 404 (platform envelope) if the code is not a
populated L2 subgroup.

```jsonc
{
  "code": "C07", "name_fa": "…", "name_en": "…",
  "group_code": "cv-htn", "group_name_fa": "فشار خون بالا", "group_name_en": "…", // primary topic
  "topics": [                            // every topic this chapter belongs to
    { "code": "cv-htn", "name_fa": "فشار خون بالا", "name_en": "…" },
    { "code": "cv-hf", "name_fa": "نارسایی قلبی", "name_en": "…" },
    { "code": "cv-angina", "name_fa": "…", "name_en": "…" },
    { "code": "cv-arrhythmia", "name_fa": "…", "name_en": "…" }
  ],
  "anatomical_name_fa": "دستگاه قلب و عروق", "anatomical_name_en": "…",  // true ATC L1, for rigour
  "drugs": [ { …full IngredientDetail incl. sections + lesson_sections… } ],
  "exam_points": [                       // built from the chapter's boxed_warning /
    { "drug_name": "acebutolol", "drug_slug": "acebutolol-149",
      "field": "contraindications",      //   contraindications / warnings summaries
      "tone": "deny",                    // boxed | deny | caution
      "point_fa": "…", "point_en": "…" }
  ],
  "progress": { "read_drug_slugs": ["acebutolol-149"], "scroll_pct": 42,
                "last_opened_at": "…" }
}
```

### `POST /lessons/chapters/{atc_code}/` — record progress

Body `{ "drug_slug"?: "…", "scroll_pct"?: 0-100 }`. Adds `drug_slug` to
`read_drug_slugs` (must belong to the chapter → else 400 `INVALID_DRUG`),
sets `scroll_pct`. Returns the same shape as GET.

---

## `/me/*` — ✅ built (Phase 3b, `apps.progress`)

All the counters below start at 0 for a new learner; the quiz and flashcard
apps (Phase 3c) bump them via `apps.progress.services`.

### `GET /me/dashboard/`

```jsonc
{
  "greeting_name": "سارا",              // LearnerProfile.display_name, else first name
  "streak_days": 4, "xp": 1280,
  "next_chapter": {                      // first ATC subgroup with done < total; null when all read
    "code": "N05", "name_fa": "…", "name_en": "…",
    "group_code": "cns-psychosis", "group_name_fa": "…", "group_name_en": "…"  // primary study topic
  },
  "focus_session": {
    "rows": [                            // rows appear only when they have content
      { "kind": "leitner", "title_fa": "…", "title_en": "…", "sub_fa": "…", "sub_en": "…",
        "minutes": 4, "count": 10 },     // only once apps.flashcards has due cards (3c)
      { "kind": "mistake", "title_fa": "…", "title_en": "…", "sub_fa": "…", "sub_en": "…",
        "minutes": 3, "mistake_id": 2 }, // top unresolved Mistake
      { "kind": "lesson",  "title_fa": "…", "title_en": "…", "sub_fa": "…", "sub_en": "…",
        "minutes": 2, "atc_code": "N05" }
    ],
    "total_minutes": 9
  }
}
```

### `GET /me/mistakes/` · `POST /me/mistakes/{id}/resolve/` · `POST /me/mistakes/restore/`

```jsonc
[{ "id": 1, "topic_key": "side_effects", "topic_fa": "عوارض جانبی",
   "topic_en": "Side effects", "count": 4, "detail_fa": "…", "detail_en": "…",
   "resolved": false, "last_seen": "…" }]
```
`resolve` marks one resolved (404 if not the caller's); `restore` un-resolves all
of the caller's and returns the full list.

### `GET /me/statistics/`

```jsonc
{ "week_bars": [40,65,50,80,45,90,70],   // minutes/day this week, index 0..6 = Sat..Fri
  "accuracy_pct": 78,                     // quiz_correct / quiz_answers
  "quizzes": 12, "reviews": 340, "minutes": 620,
  "mastery_pct": 61 }                     // chapter drug-slots read / total, across all groups
```

### `GET /me/plan/` · `PUT /me/plan/`

```jsonc
{ "days": [true,false,true,true,false,true,false],  // exactly 7; index 0..6 = Sat..Fri
  "reminders_enabled": true, "updated_at": "…" }
```
PUT replaces both fields; a `days` array that is not length 7 is 400.

### Profile

Reuse `GET /auth/me/` (carries `profile`) and `PATCH /auth/me/` for
display name / language. No separate `/me/profile/` route.

---

## Flashcards & Quiz — ✅ built, 🔒 locked (Phase 3c)

Both apps are fully built and migrated. Their routes are wired only when
`FLASHCARDS_API_ENABLED` / `QUIZ_API_ENABLED` are true (default **false**);
otherwise the maintenance router answers every path with
`503 {"code": "FEATURE_NOT_AVAILABLE"}`.

### Flashcards (`apps.flashcards`) — Leitner, no card-content table

A card is `(learner, ingredient)`; front/back are derived from the ingredient's
profile at serialization time. Boxes 1..5; intervals 0 / 3 / 7 / 16 / 35 days.

- **POST `/flashcards/seed/`** — create box-1 cards for the top ingredients that
  have ≥2 summarised card-back fields; idempotent. → `{created, deck_size}`
- **GET `/flashcards/`** — up to 20 cards with `due_at <= now`:
  `[{ id, drug_slug, box, due_at, times_seen, front_fa, front_en, back_fa, back_en }]`
  (`back_*` joins up to 3 sections: mechanism / dose / warning …)
- **GET `/flashcards/boxes/`** — `[{ box, count, due, next_due_at }]` for boxes 1..5
- **POST `/flashcards/{id}/review/`** — `{rating: "easy"|"hard"}`; `easy` → box+1,
  `hard` → box−1, reschedules by the new box's interval, and calls
  `progress.record_study(reviews=1, minutes=1, xp)`. → the updated card. 404 for
  another learner's card.

### Quiz (`apps.quiz`) — server-scored, feeds progress + mistakes

First-pass generator: ATC drug-class identification (drug→class and class→drug),
4 options each. Category narrows the drug pool (`antibiotics`→J, `cardio`→C,
`interactions`→drugs with interaction text, `general`→any). A richer generator
(contraindications / dosing / interactions) is a later pass.

- **POST `/quiz/start/`** — `{category, count}` (count ∈ 5|10|15|20) →
  `{ id, category, question_count, questions: [{ id, order, prompt_fa, prompt_en,
  options_fa[4], options_en[4] }] }` — no answer key. 422
  `INSUFFICIENT_QUESTIONS` if the pool is too small.
- **POST `/quiz/{session_id}/answer/`** — `{question_id, selected_index,
  client_answered_at?}` → `{correct, correct_index}` (server decides). 409 if the
  session is finished or the question is already answered.
- **POST `/quiz/{session_id}/finish/`** → `{score, total, mistakes_added}`;
  once only — sets the score, calls `record_quiz_answers` + `record_study(
  quizzes=1, xp=score·10)`, and `bump_mistake("drug_class", …)` per wrong answer.

### uptodate — ✅ built (Phase 6a) · read-only, no models

Served straight from the bundled UpToDate SQLite snapshot
(`settings.UPTODATE_DB_DIR`): FTS5 search in `fts.db`, zlib-JSON article bodies
in `content.db`, section names from the `toc.db` tree. English content only
(the snapshot is English). 503 `FEATURE_NOT_AVAILABLE` when the files are absent.

- **GET `/uptodate/topics/?search=&limit=`** — `[{ id, title, section, version }]`
  (topic articles only; `section` is the top-level specialty, e.g.
  "Cardiovascular Medicine"). Empty `search` → `[]`.
- **GET `/uptodate/topics/{id}/`** — `{ id, title, section, version, contributors[],
  outline_html, body_html }`. 404 if the id is unknown.

---

## Data Quality Center — ✅ rewritten (Phase 3d), not part of the app API

Internal, staff-only, server-rendered tool under `/ops/data-quality/`, wired only
when `DATA_QUALITY_CENTER_ENABLED`. It edits `summary_fa` / `summary_en` on
`drugs.IngredientProfileSection` (raw label text stays read-only); every save
needs a reason (≥ `DATA_QUALITY_MIN_REASON_LENGTH` chars) and writes an
append-only `data_quality_center.SectionEdit`. Pages: ingredient list (search +
"missing summary" filter), ingredient detail with per-section edit forms, edit
history. No JSON API, no frontend surface.

---

## Notes for later

- Quiz generator is a first pass (ATC class questions only). A richer generator
  from `IngredientProfileSection` contraindications / warnings / interactions is
  a later pass. The server already owns correctness, scoring and mistake
  attribution; the client only sends the selected index + client timestamp.
- Flashcard front/back use the ingredient (generic) name — brand/generic pairs
  from `spl_records` are a later addition.
- `xp` / `streak` live on `progress.LearnerProgress`, updated after each quiz and
  review; `league` is intentionally dropped.
