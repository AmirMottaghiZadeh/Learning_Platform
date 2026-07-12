# AI Data Pipeline

This app adds a safe, batch-based data quality pipeline for the Pharmexa drug database.

## Safety Model

AI or local rules never modify production data directly.

Flow:

1. Scan database and generate reports.
2. Generate suggestions into `ai_data_suggestions`.
3. Review suggestions manually: approve, reject, or edit.
4. Apply only approved suggestions through `ai_apply_approved`.
5. Every applied change is written to `ai_data_change_history`.
6. SQLite is backed up before applying changes.
7. Persian originals are preserved for translation suggestions; approved English translations are stored in `ai_data_translations`.

## Commands

Run health check:

```bash
rtk .venv/bin/python manage.py ai_health_check
```

Generate suggestions without applying anything:

```bash
rtk .venv/bin/python manage.py ai_generate_suggestions --provider rules --limit 200
```

Generate a useful first local cleanup batch:

```bash
rtk .venv/bin/python manage.py ai_generate_suggestions \
  --provider rules \
  --limit 500 \
  --include-normalization \
  --include-terminology \
  --include-duplicates \
  --include-medical-validation \
  --batch-name "Initial local cleanup review"
```

Preview suggestions without saving a batch:

```bash
rtk .venv/bin/python manage.py ai_generate_suggestions \
  --provider rules \
  --dry-run \
  --limit 100 \
  --include-normalization \
  --include-terminology
```

Approve safe suggestions for a batch:

```bash
rtk .venv/bin/python manage.py ai_review_suggestions --batch-id 1 --action approve --risk-level safe --reviewed-by amir
```

Reject specific suggestions:

```bash
rtk .venv/bin/python manage.py ai_review_suggestions --ids 10,11,12 --action reject --reviewed-by amir
```

Edit a suggestion before approval:

```bash
rtk .venv/bin/python manage.py ai_review_suggestions --ids 15 --action edit --edited-value "Corrected value" --reviewed-by amir
```

Approve the edited suggestion:

```bash
rtk .venv/bin/python manage.py ai_review_suggestions --ids 15 --action approve --reviewed-by amir
```

Apply approved suggestions:

```bash
rtk .venv/bin/python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

Generate a report for a batch:

```bash
rtk .venv/bin/python manage.py ai_generate_report --batch-id 1
```

## Tables

- `ai_data_batches`
- `ai_data_jobs`
- `ai_data_suggestions`
- `ai_data_change_history`
- `ai_data_reports`
- `ai_data_translations`

## Provider Architecture

Providers live in `apps/ai_data_pipeline/providers/`:

- `base.py`: provider interface, registry, and provider selection.
- `rules.py`: current deterministic local provider. Fully functional.
- `mock.py`: test provider. It remains usable for tests and local smoke checks.
- `openai.py`: placeholder only. It raises a disabled-provider error and does not call any API.
- `ollama.py`: placeholder only. It raises a disabled-provider error and does not call any API.

The active provider is configured with:

```python
AI_DATA_PIPELINE_PROVIDER = "rules"
```

Every generated suggestion stores its provider in `ai_data_suggestions.provider`. Current canonical provider names are:

- `rules`
- `mock`
- `openai`
- `ollama`
- `manual`

This project is currently in no-external-API mode. Do not use `openai` or `ollama` until a later phase explicitly enables and tests them.

## Batch And Job Model

`AIDataBatch` is the top-level grouping object. A batch groups suggestions, reports, change history, and jobs.

`AIDataJob` represents one requested pipeline task inside a batch. Job types include:

- `health_check`
- `normalization`
- `terminology_check`
- `duplicate_detection`
- `medical_validation`
- `translation`
- `full_rules_review`

Job statuses are:

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

Jobs track provider, parameters, total records, processed records, suggestions created, errors, timestamps, and creator.

## Django Admin Workflow

The pipeline is reviewable from Django Admin. Open `/admin/` and use the AI data pipeline models:

- `AI data batches`: batch status, provider/mode, related suggestions, related reports, and status summaries.
- `AI data jobs`: job status, provider, progress, suggestions created, and errors.
- `AI data suggestions`: the main review queue.
- `AI data change history`: read-only audit trail of applied changes.
- `AI data reports`: health/report summaries and report file paths.
- `AI data translations`: stored English translations; source Persian text remains unchanged.

### Reviewing Suggestions

Use the suggestion list filters to narrow the queue by:

- batch
- status
- risk level
- suggestion type
- table
- field
- provider

Use search for `table_name`, `record_id`, `field_name`, `old_value`, `suggested_value`, or `reason`.

Each suggestion page shows the old value, suggested value, reason, confidence score, risk level, provider, suggestion type, and a before/after diff view. You can edit `suggested_value`, status/risk/reason, and review metadata before apply. `table_name`, `record_id`, `field_name`, `old_value`, and `provider` are protected after creation. Applied suggestions are locked.

### Diff Review

Open a suggestion detail page in Admin and review:

- target table/record/field
- old value
- suggested value
- highlighted text diff
- reason
- confidence score
- risk level
- provider
- suggestion type

For translation suggestions with empty `suggested_value`, the local rules found Persian text but no safe local English mapping. Edit the suggested value manually before approval or reject it.

### Admin Actions

The suggestion list supports these review actions:

- approve selected suggestions
- reject selected suggestions
- mark selected suggestions as needs review

These actions only change review state. They do not modify drug records.

There is intentionally no "apply selected suggestions" action in the admin list view. Applying data changes must happen through the safe apply command so transactions, backups, old-value checks, confidence thresholds, and history logging are preserved.

### Applying Approved Suggestions Safely

After manual review, apply approved suggestions with:

```bash
rtk .venv/bin/python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

The apply command:

- creates a SQLite backup before writes
- runs inside a transaction
- applies only approved suggestions
- skips rejected, pending, edited, failed, or already applied suggestions
- skips risky suggestions unless explicitly allowed
- checks the current database value against the recorded old value
- writes every applied change to `ai_data_change_history`

### Recommended Production Workflow

1. Run `ai_health_check`.
2. Run `ai_generate_suggestions` with a limited scope.
3. Review reports in Django Admin.
4. Review suggestions in Django Admin.
5. Approve only clear, high-confidence suggestions.
6. Reject or mark uncertain suggestions as needs review.
7. Run `ai_apply_approved` during a controlled maintenance window.
8. Generate a post-apply report.
9. Keep report files and `ai_data_change_history` for audit.

## Local Rule-Based Workflow

This pipeline currently uses deterministic local rules only. It does not call OpenAI, Ollama, or any external AI API.

1. Run a database health check:

```bash
rtk .venv/bin/python manage.py ai_health_check
```

2. Generate pending rule-based suggestions:

```bash
rtk .venv/bin/python manage.py ai_generate_suggestions \
  --provider rules \
  --limit 500 \
  --include-normalization \
  --include-terminology \
  --include-duplicates \
  --include-medical-validation \
  --batch-name "Initial local cleanup review"
```

3. Open Django Admin at `/admin/`.

4. Review `AI data suggestions`.

Use filters for `batch`, `status`, `risk_level`, `suggestion_type`, `table_name`, and `field_name`. Search by old value, suggested value, or reason.

5. Approve only suggestions you trust.

Safe suggestions usually include whitespace cleanup, Arabic/Persian character normalization, simple punctuation cleanup, and exact terminology replacements from `rules/terminology_map.json`.

6. Reject uncertain or incorrect suggestions.

If a translation suggestion has an empty `suggested_value`, the local rules found Persian text but no safe English mapping. Edit it manually before approval or reject it.

7. Apply only after review:

```bash
rtk .venv/bin/python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

8. Check history and reports in Admin.

Applied changes appear in `AI data change history`. Reports are available in `AI data reports` and as JSON/HTML files under `exports/ai_data_pipeline`.

## Data Quality Center

The primary day-to-day review interface is now the dedicated internal web app at `/data-quality/`.

Use it for:

- dashboard review
- batch inspection
- job monitoring
- suggestion review and diff inspection
- record inspection
- report downloads
- health analysis

See [`apps/data_quality_center/README.md`](../data_quality_center/README.md) for URL structure, navigation, and workflow details.

## Admin Reports And Dashboard Helpers

The current admin-facing dashboard is model-based:

- Batch list shows provider, status, suggestion counts, risk counts, and a link to related suggestions.
- Batch detail shows related jobs, suggestions, reports, and change history as inlines.
- Job list shows latest job progress, provider, status, processed records, suggestions created, and errors.
- Report list shows health and suggestion summary counts and links/paths to generated JSON/HTML reports.

The report helper `build_dashboard_summary()` provides latest batches, latest jobs, health summary, and suggestion counts by status/risk/type for a future custom dashboard page.

## Local Rules Map

The configurable local terminology rules live in:

```text
apps/ai_data_pipeline/rules/terminology_map.json
```

It currently supports:

- Arabic/Persian character normalization
- Persian/Arabic digit normalization
- dosage form normalization
- common unit normalization: `mg`, `mcg`, `g`, `mL`, `IU`, `%`
- canonical timing values
- safe drug term aliases
- known English translations

## Current Provider

The default provider is `rules`. It uses deterministic normalization, terminology maps, duplicate detection, and a small local medical terminology dictionary. It is intentionally conservative. External AI providers can be added later by implementing the provider interface in `providers/base.py`, but they are not used by this workflow.

## Apply Rules

- Only `approved` suggestions are candidates for apply.
- Pending, rejected, edited, applied, or failed suggestions are not applied.
- Risky suggestions are skipped unless `--include-risky` is explicitly passed.
- Suggestions below `--min-confidence` are skipped.
- Merge/delete/medical-warning suggestions are never auto-applied by safety policy.
- Field updates are limited to an allowlist in `constants.py`.
- If the current database value differs from the suggestion's recorded old value, apply fails and the transaction rolls back.
