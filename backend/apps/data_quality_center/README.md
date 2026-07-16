# Data Quality Center

Dedicated internal web application for reviewing, validating, approving, and auditing AI and rule-based data improvements.

This is the primary operational interface for the AI data pipeline. Django Admin remains available for developer-level inspection.

## URL Structure

- `/data-quality/` - dashboard
- `/data-quality/batches/` - batch center
- `/data-quality/batches/<id>/` - batch detail
- `/data-quality/batches/<id>/compare/` - compare with previous batch
- `/data-quality/batches/<id>/generate-report/` - generate a batch report
- `/data-quality/jobs/` - job center
- `/data-quality/suggestions/` - suggestion review center
- `/data-quality/suggestions/<id>/` - diff and review detail
- `/data-quality/records/<table>/<record_id>/` - record inspector
- `/data-quality/health/` - health center
- `/data-quality/reports/` - reports list
- `/data-quality/reports/<id>/` - report detail
- `/data-quality/reports/<id>/download/json|html|csv/` - report download
- `/data-quality/database/` - drug database search and filter center
- `/data-quality/database/new/` - create a new drug with automatic identifiers
- `/data-quality/database/<id>/` - controlled drug record editor

The root URL `/` redirects to `/data-quality/`.

## Navigation

- Dashboard
- Batches
- Jobs
- Suggestions
- Health
- Reports
- Admin

## Screens Implemented

- Dashboard with health score, counts, trend sparkline, and problematic tables/fields
- Batch center with batch cards, statistics, and report actions
- Job center with progress, processed counts, duration, and errors
- Suggestion review center with filters, search, bulk actions, and diff links
- Suggestion detail page with side-by-side diff, edit-before-approval, approve/reject, and reviewer notes
- Record inspector with current values, history, warnings, and duplicates
- Health center with report summary and quality trend
- Reports list and report detail pages with JSON/HTML/CSV download
- Drug database search by column values and direct, audited editing of drug content
- New-drug entry form with automatic database IDs and generated unique external IDs

## Review Workflow

1. Generate suggestions with `manage.py ai_generate_suggestions`.
2. Open `/data-quality/suggestions/`.
3. Filter by batch, provider, status, risk, table, or field.
4. Review the diff page for each item.
5. Approve only safe items.
6. Reject uncertain or risky items.
7. Edit a suggestion before approval when the suggested value needs refinement.
8. Apply approved suggestions later through `manage.py ai_apply_approved`.

## Safety

- Suggestion approval screens do not apply production changes directly.
- Database edits are limited to drug-content fields; record identifiers and source coordinates remain read-only.
- Every changed database field is saved transactionally and written to `AIDataChangeHistory` with the staff username and before/after values.
- New drugs receive a database-generated primary key and a server-generated UUID external ID; neither identifier is entered by the user.
- Applied suggestions remain locked.

## TODO

- Add richer inline chart components.
- Add keyboard shortcuts for list review.
- Add export-to-PDF support for reports.
- Add comment threading for reviewer discussions.
- Add a dedicated record change timeline view.
