import csv
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.drugs.categories import TARGET_CATEGORIES, TARGET_CATEGORY_BY_KEY, category_for_drug
from apps.drugs.models import Drug, DrugQuestionSource
from apps.drugs.services import generic_drug_signature, normalize_option


QUESTION_TYPES = ("brandGeneric", "timing", "indication", "sideEffects")
QUESTION_TYPE_LABELS = {
    "brandGeneric": "brand/generic",
    "timing": "food timing",
    "indication": "indication",
    "sideEffects": "side effects",
}


def clean(value):
    return normalize_option(value)


def bool_text(value):
    return "yes" if value else "no"


def join_unique(values, limit=25):
    cleaned = []
    seen = set()
    for value in values:
        item = clean(value)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    if len(cleaned) > limit:
        return " | ".join(cleaned[:limit]) + f" | ... +{len(cleaned) - limit}"
    return " | ".join(cleaned)


def generic_display_name(drug):
    return clean(drug.generic_name or drug.name or drug.persian_name)


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class Command(BaseCommand):
    help = "Export a visible K_Game drug database audit report grouped by target category."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="exports/drug_audit",
            help="Directory for HTML and CSV audit files.",
        )
        parser.add_argument(
            "--category",
            choices=[category.key for category in TARGET_CATEGORIES],
            help="Limit export to a single target category.",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"]).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        selected_category = options.get("category")
        drugs = list(Drug.objects.all().order_by("id"))
        if selected_category:
            drugs = [
                drug
                for drug in drugs
                if category_for_drug(drug).key == selected_category
            ]
        drug_ids = [drug.id for drug in drugs]

        active_source_counts = defaultdict(Counter)
        total_source_counts = defaultdict(Counter)
        for source in DrugQuestionSource.objects.filter(drug_id__in=drug_ids):
            total_source_counts[source.drug_id][source.question_type] += 1
            if source.is_active:
                active_source_counts[source.drug_id][source.question_type] += 1

        summary = self.build_summary(drugs, active_source_counts)
        records = self.build_records(drugs, active_source_counts, total_source_counts)
        generic_groups = self.build_generic_groups(drugs, active_source_counts)
        quality_issues = self.build_quality_issues(drugs, active_source_counts)

        write_csv(
            output_dir / "category_summary.csv",
            [
                "category_key",
                "category_label",
                "drug_rows",
                "unique_generics",
                "rows_missing_generic_identity",
                "brandGeneric_sources",
                "timing_sources",
                "indication_sources",
                "sideEffects_sources",
            ],
            summary,
        )
        write_csv(output_dir / "drug_records.csv", list(records[0].keys()) if records else [], records)
        write_csv(
            output_dir / "generic_groups.csv",
            list(generic_groups[0].keys()) if generic_groups else [],
            generic_groups,
        )
        write_csv(
            output_dir / "quality_issues.csv",
            list(quality_issues[0].keys()) if quality_issues else [
                "issue_type",
                "category_key",
                "category_label",
                "external_id",
                "generic_display",
                "brand_name",
                "detail",
            ],
            quality_issues,
        )
        self.write_html(output_dir / "drug_audit.html", summary, records, generic_groups, quality_issues)

        self.stdout.write(
            self.style.SUCCESS(
                "Drug audit exported to "
                f"{output_dir} "
                f"({len(drugs)} drug rows, {len(generic_groups)} generic groups, "
                f"{len(quality_issues)} quality issues)."
            )
        )

    def build_summary(self, drugs, active_source_counts):
        by_category = {
            category.key: {
                "category_key": category.key,
                "category_label": category.label,
                "drug_rows": 0,
                "unique_generics": set(),
                "rows_missing_generic_identity": 0,
                "brandGeneric_sources": 0,
                "timing_sources": 0,
                "indication_sources": 0,
                "sideEffects_sources": 0,
            }
            for category in TARGET_CATEGORIES
        }
        for drug in drugs:
            category = category_for_drug(drug)
            row = by_category[category.key]
            row["drug_rows"] += 1
            generic_sig = generic_drug_signature(drug)
            if generic_sig:
                row["unique_generics"].add(generic_sig)
            else:
                row["rows_missing_generic_identity"] += 1
            for question_type in QUESTION_TYPES:
                row[f"{question_type}_sources"] += active_source_counts[drug.id][question_type]

        summary = []
        for category in TARGET_CATEGORIES:
            row = by_category[category.key]
            if not row["drug_rows"]:
                continue
            row = row.copy()
            row["unique_generics"] = len(row["unique_generics"])
            summary.append(row)
        return summary

    def build_records(self, drugs, active_source_counts, total_source_counts):
        records = []
        for drug in drugs:
            category = category_for_drug(drug)
            active_counts = active_source_counts[drug.id]
            total_counts = total_source_counts[drug.id]
            records.append(
                {
                    "category_key": category.key,
                    "category_label": category.label,
                    "generic_signature": generic_drug_signature(drug),
                    "generic_display": generic_display_name(drug),
                    "external_id": drug.external_id,
                    "brand_name": clean(drug.brand_name),
                    "name": clean(drug.name),
                    "persian_name": clean(drug.persian_name),
                    "dosage_form": clean(drug.dosage_form),
                    "drug_classification": clean(drug.drug_classification),
                    "source_topic": clean(drug.source_topic),
                    "source_file": clean(drug.source_file),
                    "consumption_time_sorted": clean(drug.consumption_time_sorted),
                    "consumption_time": clean(drug.consumption_time),
                    "indication_answer": clean(drug.indication_answer),
                    "side_effects_answer": clean(drug.side_effects_answer),
                    "has_brandGeneric": bool_text(active_counts["brandGeneric"]),
                    "has_timing": bool_text(active_counts["timing"]),
                    "has_indication": bool_text(active_counts["indication"]),
                    "has_sideEffects": bool_text(active_counts["sideEffects"]),
                    "active_brandGeneric_sources": active_counts["brandGeneric"],
                    "active_timing_sources": active_counts["timing"],
                    "active_indication_sources": active_counts["indication"],
                    "active_sideEffects_sources": active_counts["sideEffects"],
                    "total_question_sources": sum(total_counts.values()),
                    "active_question_sources": sum(active_counts.values()),
                }
            )
        return records

    def build_generic_groups(self, drugs, active_source_counts):
        groups = {}
        for drug in drugs:
            generic_sig = generic_drug_signature(drug)
            if not generic_sig:
                continue
            category = category_for_drug(drug)
            key = (category.key, generic_sig)
            if key not in groups:
                groups[key] = {
                    "category_key": category.key,
                    "category_label": category.label,
                    "generic_signature": generic_sig,
                    "generic_display": generic_display_name(drug),
                    "drug_rows": 0,
                    "brand_names": [],
                    "external_ids": [],
                    "dosage_forms": [],
                    "classifications": [],
                    "source_topics": [],
                    "brandGeneric_sources": 0,
                    "timing_sources": 0,
                    "indication_sources": 0,
                    "sideEffects_sources": 0,
                }
            group = groups[key]
            group["drug_rows"] += 1
            group["brand_names"].append(drug.brand_name)
            group["external_ids"].append(drug.external_id)
            group["dosage_forms"].append(drug.dosage_form)
            group["classifications"].append(drug.drug_classification)
            group["source_topics"].append(drug.source_topic or drug.source_file)
            for question_type in QUESTION_TYPES:
                group[f"{question_type}_sources"] += active_source_counts[drug.id][question_type]

        rows = []
        for group in groups.values():
            row = group.copy()
            row["brand_names"] = join_unique(row["brand_names"])
            row["external_ids"] = join_unique(row["external_ids"], limit=40)
            row["dosage_forms"] = join_unique(row["dosage_forms"])
            row["classifications"] = join_unique(row["classifications"])
            row["source_topics"] = join_unique(row["source_topics"])
            rows.append(row)

        rows.sort(key=lambda row: (row["category_key"], row["generic_display"].casefold()))
        return rows

    def build_quality_issues(self, drugs, active_source_counts):
        issues = []
        for drug in drugs:
            category = category_for_drug(drug)
            generic_display = generic_display_name(drug)
            base = {
                "category_key": category.key,
                "category_label": category.label,
                "external_id": drug.external_id,
                "generic_display": generic_display,
                "brand_name": clean(drug.brand_name),
            }
            if not generic_drug_signature(drug):
                issues.append(
                    {
                        **base,
                        "issue_type": "missing_generic_identity",
                        "detail": "No generic_name, name, or persian_name is available.",
                    }
                )
            if category.key == "other":
                issues.append(
                    {
                        **base,
                        "issue_type": "uncategorized_other",
                        "detail": clean(drug.source_topic or drug.source_file or drug.drug_classification),
                    }
                )
            if sum(active_source_counts[drug.id].values()) == 0:
                issues.append(
                    {
                        **base,
                        "issue_type": "no_active_question_sources",
                        "detail": "No active question source exists for this drug row.",
                    }
                )
            for question_type in QUESTION_TYPES:
                if active_source_counts[drug.id][question_type]:
                    continue
                issues.append(
                    {
                        **base,
                        "issue_type": f"missing_{question_type}",
                        "detail": f"Missing active {QUESTION_TYPE_LABELS[question_type]} source.",
                    }
                )
        issues.sort(key=lambda row: (row["category_key"], row["issue_type"], row["generic_display"]))
        return issues

    def write_html(self, path, summary, records, generic_groups, quality_issues):
        summary_rows = "\n".join(self.table_row(row) for row in summary)
        record_rows = "\n".join(self.table_row(row) for row in records)
        group_rows = "\n".join(self.table_row(row) for row in generic_groups)
        issue_rows = "\n".join(self.table_row(row) for row in quality_issues)

        html = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>K_Game Drug Audit</title>
  <style>
    body {{
      margin: 0;
      font-family: Calibri, "B Nazanin", "B Mitra", Arial, sans-serif;
      background: #f6f6f2;
      color: #241a2a;
    }}
    header {{
      padding: 24px 32px;
      background: #e7e8e3;
      border-bottom: 1px solid #d8d6dc;
    }}
    main {{ padding: 24px 32px; }}
    h1, h2 {{ margin: 0 0 12px; }}
    section {{ margin-bottom: 32px; }}
    .meta {{ color: #6c6375; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      direction: ltr;
      background: #fff;
      border: 1px solid #ddd9e2;
      font-size: 13px;
    }}
    th, td {{
      padding: 8px 10px;
      border-bottom: 1px solid #eeeaf1;
      vertical-align: top;
      text-align: left;
      max-width: 360px;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #403147;
      color: #fff;
      z-index: 1;
    }}
    tr:nth-child(even) td {{ background: #fbfafc; }}
    .table-wrap {{
      max-height: 72vh;
      overflow: auto;
      border-radius: 8px;
    }}
    .links a {{
      display: inline-block;
      margin: 0 0 8px 8px;
      color: #582b8c;
    }}
  </style>
</head>
<body>
  <header>
    <h1>K_Game Drug Database Audit</h1>
    <div class="meta">Grouped by target drug category. CSV files are in the same folder.</div>
  </header>
  <main>
    <section class="links">
      <a href="category_summary.csv">category_summary.csv</a>
      <a href="drug_records.csv">drug_records.csv</a>
      <a href="generic_groups.csv">generic_groups.csv</a>
      <a href="quality_issues.csv">quality_issues.csv</a>
    </section>
    <section>
      <h2>Category Summary</h2>
      <div class="table-wrap"><table>{self.table_head(summary)}<tbody>{summary_rows}</tbody></table></div>
    </section>
    <section>
      <h2>Generic Groups</h2>
      <div class="table-wrap"><table>{self.table_head(generic_groups)}<tbody>{group_rows}</tbody></table></div>
    </section>
    <section>
      <h2>Quality Issues</h2>
      <div class="table-wrap"><table>{self.table_head(quality_issues)}<tbody>{issue_rows}</tbody></table></div>
    </section>
    <section>
      <h2>Drug Records</h2>
      <div class="table-wrap"><table>{self.table_head(records)}<tbody>{record_rows}</tbody></table></div>
    </section>
  </main>
</body>
</html>
"""
        path.write_text(html, encoding="utf-8")

    def table_head(self, rows):
        if not rows:
            return "<thead></thead>"
        cells = "".join(f"<th>{escape(str(field))}</th>" for field in rows[0].keys())
        return f"<thead><tr>{cells}</tr></thead>"

    def table_row(self, row):
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row.values())
        return f"<tr>{cells}</tr>"
