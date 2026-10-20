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

New accounts sign up with a mobile number: an SMS code (sms.ir verify
template) signs them in the first time, they then choose a password
(`User.has_password` is false until they do), and every later sign-in is
number + password. A forgotten password is reset with another SMS code.
Codes are stored hashed, expire after `OTP_TTL_SECONDS`, allow
`OTP_MAX_ATTEMPTS` wrong tries, and a number gets one at most every
`OTP_RESEND_SECONDS` and `OTP_MAX_PER_PHONE_PER_DAY` times a day.

| Method | Path | Status | Notes |
|---|---|---|---|
| POST | `/auth/otp/request/` | ✅ | `{phone, purpose: "signup"\|"reset"}` → `{phone, code_length, expires_in, resend_in}`; texts an SMS code. 409 `PHONE_REGISTERED` (signup, number already has a password), 404 `PHONE_NOT_REGISTERED` (reset), 429 `OTP_TOO_SOON` (`details.retry_after`) / `OTP_DAILY_LIMIT`, 503 `SMS_SEND_FAILED` |
| POST | `/auth/otp/verify/` | ✅ | `{phone, purpose, code, device_name?}` → `AuthTokenResponse` (201 when the account was just created). 400 `OTP_INVALID` (`details.attempts_left`) / `OTP_EXPIRED` / `OTP_LOCKED`. The session may set a password without the current one for `AUTH_STEP_UP_TTL_MINUTES` |
| POST | `/auth/password/set/` | ✅ | `{new_password, new_password_confirm, name?, current_password?}` → `User`. `current_password` needed only if the account already has a password and the session didn't just verify an SMS code; signs every other session out |
| POST | `/auth/register/` | ⛔ | email sign-up, 403 `EMAIL_REGISTRATION_CLOSED` unless `AUTH_EMAIL_REGISTRATION_ENABLED` |
| POST | `/auth/login/` | ✅ | `{username, password, device_name?}` → `AuthTokenResponse`; `username` = mobile number (any spelling), email, or username |
| POST | `/auth/refresh/` | ✅ | `{refresh_token}` → `AuthTokenResponse` (refresh rotates) |
| POST | `/auth/logout/` · `/auth/logout-all/` | ✅ | revoke current / all sessions |
| GET | `/auth/me/` | ✅ | → `User` (incl. `profile`) |
| PATCH | `/auth/me/` | ✅ | body = partial `LearnerProfile` (e.g. `{display_name}`) → `User` |
| POST | `/auth/onboarding/` | ✅ | `{study_field, study_goal, study_level, display_name?, language?}` → `User`; sets `profile.onboarded_at` |
| GET | `/auth/sessions/` · POST `/auth/sessions/{id}/revoke/` | ✅ | device list / revoke |
| POST | `/auth/step-up/` | ✅ | re-verify password for sensitive actions |
| GET/POST | `/auth/password-reset/` · `/auth/password-reset/confirm/` | ✅ | email reset, for accounts made with an email |
| GET | `/auth/roles/` · `/auth/role-assignments/` · `/auth/security-events/` | ✅ | RBAC / audit (staff) |

```jsonc
// User
{
  "id": 1, "username": "sara", "email": "sara@example.com",
  "first_name": "Sara", "last_name": "Karimi",
  "roles": ["learner"],
  "profile": {                     // LearnerProfile
    "display_name": "Sara Karimi",
    "study_field": "pharmacy",     // "" | pharmacy | medicine (nursing: legacy)
    "study_goal": "comprehensive", // "" | comprehensive | final | clinical (residency: legacy)
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

Each topic also carries a `category_code`/`category_name_*` — one of 12 broad
body-system/domain groups in `STUDY_TOPICS.CATEGORIES` (e.g. "Cardiovascular &
blood", "Endocrine & metabolism"), purely so a client can cluster the 50+
flat topics into a shorter list to pick from first (`LessonsScreen`:
category accordion → topic accordion → chapter). A topic the coverage
fallback above produced is filed under the `"misc"` category.

### `GET /lessons/groups/` — the study tree with progress

```jsonc
[{ "code": "cv-htn", "name_fa": "فشار خون بالا", "name_en": "Hypertension",
   "category_code": "cardio-blood", "category_name_fa": "قلب، عروق و خون",
   "category_name_en": "Cardiovascular & blood",
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
  "drugs": [                             // the list only -- names, no lesson
    { "slug": "acebutolol-149", "name": "acebutolol",    //   content (see below)
      "pharm_classes": ["beta-Adrenergic Blocker"],
      "atc_group": { "code": "C07AB", "name_fa": "…", "name_en": "Beta blocking agents, selective" } }
  ],                                     // ordered by atc_group.code: a group is one run
  "progress": { "read_drug_slugs": ["acebutolol-149"], "scroll_pct": 42,
                "last_opened_at": "…" }
}
```

`read_drug_slugs` is computed from a **global per-user read set**
(`lessons.ReadDrug`), filtered to this chapter's ingredients — not a
per-chapter stored list. Reading a drug that carries more than one ATC code
(aspirin, for real: A01 dental, B01 antithrombotic, N02 analgesic) marks it
read everywhere it appears, so re-opening the same drug through a different,
unrelated chapter shows it already read instead of asking the learner to read
it again. `scroll_pct`/`last_opened_at` stay per-chapter on `ChapterProgress`.

### `GET /lessons/search/?q=` — find a drug by name

The lessons' quick find. Matches `q` (at least 2 characters) against each
drug's English `name` and Persian `name_fa`, with Persian spellings folded
together (ي/ی, ك/ک, آ/ا, zero-width non-joiner or space inside a name,
diacritics). Best first: exact, then prefix, then a later word's start, then
anywhere; at most 20. Drugs in no lesson chapter are left out. Requires the
`lessons` feature.

```jsonc
[
  { "slug": "aspirin-1191", "name": "aspirin", "name_fa": "آسپرین",
    "chapters": [                          // every chapter it's taught in;
      { "code": "A01", "name_fa": "…", "name_en": "…" },   // the first opens it
      { "code": "B01", "name_fa": "…", "name_en": "…" }
    ] }
]
```

### `GET /lessons/drugs/{slug}/` — one drug's lesson

Fetched when the learner opens a drug from a chapter's list. 404 (platform
envelope) for an unknown slug.

```jsonc
{
  "rxcui": "149", "name": "acebutolol", "slug": "acebutolol-149", "n_products": 7,
  "n_source_records": 30, "pharm_classes": ["…"], "atc_codes": [{ "code": "C07AB04", "name": "…", "level": 5 }],
  "sections": [                          // per-field flags only (badges); no
    { "field": "boxed_warning", "label": "Boxed warning", "has_summary": true }
  ],                                     //   summaries or raw_text
  "lesson_sections": [ … ]               // as in /drugs/{slug}/ -- the lesson text
}
```

### `POST /lessons/chapters/{atc_code}/` — record progress

Body `{ "drug_slug"?: "…", "scroll_pct"?: 0-100 }`. Adds `drug_slug` to the
learner's global read set (must belong to the current chapter → else 400
`INVALID_DRUG`), sets `scroll_pct` on this chapter's `ChapterProgress`.
Returns the same shape as GET.

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

### Flashcards (`apps.flashcards`) — Leitner

A card is `(learner, ingredient)`. What it says comes from `FlashcardFact`, which
is empty until the content made by the study-content pipeline is loaded (the
earlier rule-based builder was retired), in five sections: `indication`, `adr_common`, `adr_serious`, `dosage_forms`,
`contra_boxed` (boxed warning, then contraindications). Boxes 1..5; intervals
0 / 3 / 7 / 16 / 35 days.

- **POST `/flashcards/seed/`** — create box-1 cards for the top ingredients that
  have ≥2 card sections; idempotent. → `{created, deck_size}`
- **GET `/flashcards/`** — up to 20 cards with `due_at <= now`:
  `[{ id, drug_slug, box, due_at, times_seen, front_fa, front_en, back_fields_fa, back_fields_en }]`
  where each `back_fields_*` entry is one section in the order above:
  `{ field, label, tone, items: [≤3 facts], text: items joined by "\n" }`
- **GET `/flashcards/boxes/`** — `[{ box, count, due, next_due_at }]` for boxes 1..5
- **POST `/flashcards/{id}/review/`** — `{rating: "easy"|"hard"}`; `easy` → box+1,
  `hard` → box−1, reschedules by the new box's interval, and calls
  `progress.record_study(reviews=1, minutes=1, xp)`. → the updated card. 404 for
  another learner's card.

**Topic decks** — the learner picks a category, then a topic (the lessons
taxonomy's `CATEGORIES` / `STUDY_TOPICS`), and works through that topic's carded
drugs one by one in a fixed order (L2 order, then name) until the deck ends.
Progress is a `TopicProgress` row per (learner, topic).

- **GET `/flashcards/decks/`** — `{ topics_finished, cards_reviewed, categories:
  [{ key, name_fa, name_en, topics_finished, topics: [{ key, name_fa, name_en,
  total, position, finished }] }] }`; topics with no carded drug, and categories
  with no such topic, are left out.
- **GET `/flashcards/decks/{topic}/`** — `{ key, name_fa, name_en, category_key,
  category_name_fa, category_name_en, total, position, known, hard, finished,
  next_topic, cards: [same card shape as above, without id/box] }`. 404 for an
  unknown topic.
- **POST `/flashcards/decks/{topic}/answer/`** — `{drug_slug, rating}`; reviews the
  drug's Leitner card (created if missing) and records study; moves `position`
  on only when `drug_slug` is the card at `position`. → `{ total, position, known,
  hard, finished, next_topic }`, where `next_topic` (`{ key, name_fa, name_en,
  category_key, category_name_fa, category_name_en }`, or null after the last
  topic) is set once the deck is finished. 422 `NOT_IN_DECK` for a drug outside
  the topic.
- **POST `/flashcards/decks/{topic}/restart/`** — resets the topic's pass. → the
  same progress shape.

### Quiz (`apps.quiz`) — server-scored, feeds progress + mistakes

Questions come from a pre-built bank (`BankQuestion`), which is empty until the
content made by the study-content pipeline is loaded (the earlier rule-based
generator was retired); until then `POST /quiz/start/` answers 422
`INSUFFICIENT_QUESTIONS`. A question's `field` is its card section.

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

Quiz prompts preserve the full bank text in both languages, including clinical
scenarios longer than 300 characters. Deployments must apply quiz migration
`0009_alter_quizquestion_prompts` to widen existing session question columns.

With billing enforcement enabled, starting a quiz checks plan access; answering
a question also checks and consumes the question allowance. A successful start
can therefore be followed by 402 `QUOTA_EXCEEDED` on answering. Missing bearer
credentials instead return 401 `NOT_AUTHENTICATED`. Check the response of the
actual authenticated POST when diagnosing a 402; opening its URL directly in a
browser does not send the app's bearer token.

### uptodate — ✅ built (Phase 6a) · read-only, no models

Served straight from the bundled UpToDate SQLite snapshot
(`settings.UPTODATE_DB_DIR`): FTS5 search in `fts.db`, zlib-JSON article bodies
in `content.db`, section names from the `toc.db` tree. English content only
(the snapshot is English). 503 `FEATURE_NOT_AVAILABLE` when the files are absent.

- **GET `/uptodate/topics/?search=&limit=`** — `[{ id, title, section, version,
  updated, snippet }]` (topic articles only; `section` is the top-level
  specialty, e.g. "Cardiovascular Medicine"; `updated` is the topic's own
  "last updated" date such as "Feb 11, 2026", or ""; `snippet` is plain text
  around the first query hit in the article body, skipping the title/author
  header). Empty `search` → `[]`.
- **GET `/uptodate/topics/{id}/`** — `{ id, title, section, version, updated,
  contributors[], outline_html, body_html }`. 404 if the id is unknown.

---

## Data Quality Center — ✅ review workflow, not part of the app API

Internal, staff-only, server-rendered Persian console under `/ops/data-quality/`
(on unless `DATA_QUALITY_CENTER_ENABLED=False`; in production
`https://api.pharmenta.ir/ops/data-quality/`). Its own sign-in page
(`login/`) admits active staff only, throttles repeated failures per IP and
records `accounts.SecurityAuditEvent` login events.

It edits `summary_fa` / `summary_en` on `drugs.IngredientProfileSection`; the
raw label text stays read-only. Workflow (`data_quality_center.services`):

- an operator's edits autosave as a **draft** (`drugs/<slug>/<field>/draft/`,
  answers with the automatic checks and word diff as JSON), then
  **submit** with a reason (≥ `DATA_QUALITY_MIN_REASON_LENGTH` chars) →
  **pending**; a pending request can be **withdrawn** to draft, and a draft
  **discarded**;
- only a superuser decides, on the review desk (`review/`): **approve**
  (applies the summaries and writes the append-only `SectionEdit`; refused if
  the section changed since submission), **request changes** (back to the
  operator with a note, edited and resubmitted) or **reject**;
- a superuser can **revert** an applied edit from the history page, which
  opens a pending request restoring the earlier text.

One open (pending / changes-requested) request per section, one draft per
operator per section. Every action after the first submission writes an
append-only `ReviewEvent` (actor, time, note, IP), shown as each request's
timeline and on `history/`. Automatic checks (warnings only): numbers in the
summary missing from the label, empty Persian/English summary, only one
language changed, summary longer than its source.

---

## Billing — ✅ built (`apps.billing`), enforcement on in production

A **plan** (`kind: "plan"`, a subscription tier) or **product** (`kind:
"product"`, sold on its own) is a set of **features**, each optionally capped
per day or month (Tehran calendar; months are Jalali months), with one price
per duration (`duration_days`, `null` = permanent). Buying one grants an
**entitlement** holding a snapshot of the plan's features at that moment, so
editing a plan only reaches later buyers. The plan with `is_free` is what
everyone has, read live. When two sources give the same feature the more
generous wins (unlimited beats any cap; between caps the larger monthly
equivalent). Built-in feature keys: `lessons`, `uptodate`, `lexicomp`,
`medscape`, `calculators`, `flashcards`, `quiz`, `stats`; operators add
`content` features (fence off a study category or an ATC prefix, enforced at
once) and `custom` ones (enforced only once code checks the key).

- **GET `/billing/catalog/`** — `{ free, plans[], products[] }`, each
  `{ id, kind, slug, name_fa, name_en, tagline_fa, audience, is_free,
  prices: [{ id, duration_days, duration_label, price_toman }],
  features: [{ key, name_fa, limit, period, unit_fa }] }`. Only plans with
  status `active` are listed (hidden ones are granted by an operator only).
- **GET `/billing/me/`** — `{ enforced, features: [{ key, name_fa, limit,
  period, used }], entitlements: [{ id, plan_name_fa, plan_kind, source,
  starts_at, ends_at, days_left }] }`.
- **POST `/billing/quote/`** — `{ price_id, discount_code? }` →
  `{ amount_toman, discount_toman, payable_toman }`; 400 with
  `PRICE_NOT_AVAILABLE` or a `DISCOUNT_*` code.
- **POST `/billing/checkout/`** — same body → 201 `{ order_id, status,
  payment_url }`. Open `payment_url` in the browser; a free order (100% off)
  comes back `status: "paid"` with no URL. 502 `GATEWAY_ERROR` when the
  gateway is unreachable.
- **GET `/billing/callback/`** — where the gateway returns the learner
  (`?Authority=…&Status=OK|NOK`). Verifies with the gateway, grants access
  once (a retried callback changes nothing) and shows a Persian result page
  linking to `BILLING_RETURN_URL`. HTML, not JSON.
- **GET `/billing/orders/`** — the learner's last 50 orders.

With billing enforcement enabled (the production default; it can also be
controlled from the billing console), content endpoints answer **402**:
`PREMIUM_REQUIRED` (`details.feature`) when no plan of the learner includes
the feature or a content feature fences the content, `QUOTA_EXCEEDED`
(`details: { feature, limit, period, used }`) when a cap is used up. A cap
counts each item (article, calculator, card, question) once per period;
searching and browsing lists stay open, opening an item counts. Staff are
never locked. Gateways: Zarinpal, SEP and Zibal, configured on the console's
«درگاه پرداخت» page (merchant or terminal id, callback URL, return URL, the
enforcement switch and a sales switch; saving asks for the operator's password
again and is audited), each value falling back to `BILLING_GATEWAY` / the
matching gateway environment settings (`ZARINPAL_MERCHANT_ID`,
`ZARINPAL_SANDBOX`, `ZIBAL_MERCHANT`, `ZIBAL_SANDBOX`) /
`BILLING_RETURN_URL` / `BILLING_ENFORCEMENT_ENABLED`
when the console leaves it unset. With sales switched off, checkout answers
503 `SALES_PAUSED`. `fake` is for development only and refused in
production.

### Guest access — off unless switched on in the console

While the console's «تنظیمات دسترسی» switch is on (`/ops/access/`), the app
opens without signing in, e.g. for a reviewer checking the site:

- **GET `/guest/status/`** — no auth → `{ enabled }`.
- **POST `/guest/session/`** — no auth, throttled per IP (`guest_session`,
  default 20/hour) → 201, the same body as login, for a new throwaway
  account (`user.is_guest: true`, onboarded, no password). 403
  `GUEST_ACCESS_DISABLED` when the switch is off.

Guests hold only the free plan, cannot buy (403 `GUEST_CANNOT_BUY` from
quote/checkout) and are left out of the console's users list. Switching
guest access off deactivates every guest and revokes their sessions;
`python manage.py delete_guest_accounts` (or the console button) then
removes them. `UserSerializer` carries `is_guest` for every account.

### Billing console — superuser only, `/ops/`

Server-rendered Persian console (on unless `BILLING_CONSOLE_ENABLED=False`;
in production `https://api.pharmenta.ir/ops/`), its own sign-in page
(`/ops/login/`, superusers only, throttled per IP). Users (search, segments,
a drawer per user, full record with access, usage, payments, devices and
roles; grant, extend, revoke, block, sign out everywhere; CSV export), the
plan builder (basics → features and caps → prices → publish), features
(edit, switch off, define new content or custom ones), the payment gateway
(settings plus a connection test that asks Zarinpal for an unpaid 1,000-Toman
payment), discount codes
(Jalali dates), sales and the audit log of every console action
(`billing.AdminAction`).

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
