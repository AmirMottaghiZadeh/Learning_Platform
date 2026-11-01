#!/usr/bin/env python3
"""Build the phase-0 judging workbook for docs/search/eval/dev-queries.csv.

Candidates are pooled from three sources so that no future engine decides
what the reviewer sees: the drug monograph, UpToDate's own concept ranking
(search.db query/query_topic) and the current baseline engine. They are shown
in a seeded random order without their source. pool_* columns are pooling
hints only and must never be read by the search engine.

The workbook contains UpToDate titles and headings, so it is written outside
the repository. Run with a Python that has openpyxl, e.g.:

    python3 docs/search/eval/build_judging_workbook.py \
        --source /home/amir/Documents/UpToDate \
        --output-dir /home/amir/Documents/pharmenta-search-eval
"""

import argparse
import csv
from datetime import date
import hashlib
from pathlib import Path
import random
import sqlite3
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_hierarchy import HierarchicalRetriever, article_sections  # noqa: E402
from apps.uptodate.search_hierarchy_source import SQLiteHierarchySource  # noqa: E402

MAX_ARTICLES = 5
MAX_SECTIONS = 5
AUDIENCE = {"a": "a_topic_hits", "p": "p_topic_hits", "i": "i_topic_hits", "x": "x_topic_hits"}
LEVELS = {"article": "مقاله", "section": "بخش", "paragraph": "پاراگراف",
          "lexicomp": "ارجاع به بررسی تداخل Lexicomp", "ambiguous": "مبهم: چند نامزد"}
KINDS = {"drug_general": "مونوگراف دارو", "drug_pediatric": "مونوگراف اطفال",
         "drug_patient": "اطلاعات دارویی بیمار", "clinical_topic": "مقالهٔ بالینی",
         "patient_topic": "آموزش بیمار", "navigation_topic": "پیوند راهنما یا ماشین‌حساب"}
CATEGORIES = ("drug_only", "disease_only", "drug_topic", "disease_goal", "disease_context",
              "detail", "interaction", "colloquial", "ambiguous", "english")

FONT = "Arial"
HEAD_FILL = PatternFill("solid", start_color="D9E2F3")
EDIT_FILL = PatternFill("solid", start_color="FFF2CC")
BAND_FILL = PatternFill("solid", start_color="F2F2F2")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))


def concept_topics(search, term, audience, limit=3):
    column = AUDIENCE[audience]
    for (concept,) in search.execute(
            "SELECT id FROM query WHERE word = ? COLLATE NOCASE ORDER BY weight DESC", (term,)):
        row = search.execute(f"SELECT {column} FROM query_topic WHERE id = ?", (concept,)).fetchone()
        if row and row[0]:
            return [topic for topic in row[0].split(",") if topic][:limit]
    raise SystemExit(f"Concept not found in search.db: {term!r}")


def monographs(source, drug, population):
    wanted = [f"{drug}: Pediatric drug information"] if population == "p" else []
    wanted.append(f"{drug}: Drug information")
    by_title = {article.title.casefold(): article.article_id for article in source.catalog.articles}
    found = [by_title[title.casefold()] for title in wanted if title.casefold() in by_title]
    if not found:
        raise SystemExit(f"Monograph not found: {drug!r}")
    return found


def pool(source, search, engine, row):
    sources, baseline_sections = {}, {}
    def add(article_id, label):
        if article_id in source.metadata:
            sources.setdefault(article_id, []).append(label)
    if row["pool_drug"]:
        for article_id in monographs(source, row["pool_drug"], row["population"]):
            add(article_id, "monograph")
    for term in filter(None, (t.strip() for t in row["pool_concepts"].split(";"))):
        for rank, article_id in enumerate(concept_topics(search, term, row["population"] or "a"), 1):
            add(article_id, f"concept:{term}:{rank}")
    try:
        result = engine.search(row["query"])
        for trace in result["articles"][:2]:
            add(trace["article_id"], "baseline")
            baseline_sections[trace["article_id"]] = [s["section_id"] for s in trace["selected_sections"]]
    except ValueError:
        pass
    return dict(list(sources.items())[:MAX_ARTICLES]), baseline_sections


def section_candidates(source, article_id, keys, baseline=()):
    article, outline = source.load_article(article_id)
    sections = article_sections(outline, article)
    keys = [key.strip().casefold() for key in keys.split(";") if key.strip()]
    matched = [s for s in sections if s.section_id in baseline
               or any(key in " > ".join(s.path_titles).casefold() for key in keys)]
    if matched:
        return matched[:MAX_SECTIONS], ""
    return [s for s in sections if len(s.path_ids) == 1][:10], "واژهٔ کلیدی پیدا نشد؛ بخش‌های سطح اول"


def style_sheet(ws, headers, widths, editable):
    ws.sheet_view.rightToLeft = True
    ws.append(headers)
    for index, (cell, width) in enumerate(zip(ws[1], widths), 1):
        cell.font = Font(name=FONT, bold=True)
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[cell.column_letter].width = width
    ws.freeze_panes = "A2"
    return [headers.index(name) + 1 for name in editable]


def finish_rows(ws, editable_columns, band_key_column):
    ws.auto_filter.ref = ws.dimensions
    band, previous = False, None
    for row in ws.iter_rows(min_row=2):
        key = row[band_key_column - 1].value
        if key != previous:
            band, previous = not band, key
        for cell in row:
            cell.font = Font(name=FONT)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = THIN
            if cell.column in editable_columns:
                cell.fill = EDIT_FILL
            elif band:
                cell.fill = BAND_FILL


def add_list(ws, values, column, last_row):
    validation = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
    ws.add_data_validation(validation)
    validation.add(f"{column}2:{column}{max(last_row, 2)}")


def guide_sheet(wb, today, counts):
    ws = wb.create_sheet("راهنما", 0)
    ws.sheet_view.rightToLeft = True
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 90
    lines = [
        ("کاربرگ داوری جست‌وجوی هوشمند — فاز ۰", ""),
        ("تاریخ ساخت", today),
        ("هدف", "تعیین جواب درست هر سؤال توسعه. موتور جست‌وجو بعداً با همین داوری سنجیده می‌شود."),
        ("ترتیب کار", "۱) برگهٔ «سؤال»: سؤال‌ها را مرور کنید؛ حذف، بازنویسی یا تأیید عمق. "
                     "۲) برگهٔ «مقاله»: به هر نامزد درجه بدهید. ۳) برگهٔ «بخش»: برای سؤال‌های بخشی و پاراگرافی."),
        ("سلول‌های قابل ویرایش", "فقط ستون‌های زرد. بقیهٔ ستون‌ها را تغییر ندهید."),
        ("درجه ۲", "همان جوابی که داروساز برای این سؤال باز می‌کند."),
        ("درجه ۱", "مرتبط و قابل قبول، ولی بهترین نیست."),
        ("درجه ۰", "نامرتبط یا نامناسب."),
        ("اگر هیچ نامزدی درست نیست", "در ستون «یادداشت» یکی از ردیف‌های همان سؤال، عنوان مقاله یا بخش درست را بنویسید."),
        ("ترتیب نامزدها", "تصادفی است و منبع نامزد عمداً نشان داده نمی‌شود؛ ردیف بالاتر به معنی بهتر بودن نیست."),
        ("سؤال‌های تداخل", "عمق «ارجاع به بررسی تداخل Lexicomp» یعنی پیشنهاد می‌شود این سؤال‌ها به ابزار تداخل Lexicomp اپ بروند. "
                          "در برگهٔ «سؤال» درست یا نادرست بودن این تصمیم را مشخص کنید."),
        ("سؤال‌های مبهم", "همهٔ نامزدهای قابل قبول را ۱ یا ۲ بدهید؛ جواب خوب برای این سؤال‌ها نمایش چند گزینه است."),
        ("مثال یک ردیف داوری‌شده", "d023 | عوارض متفورمین | Metformin: Drug information | مونوگراف دارو | درجه: 2"),
        ("مثال بخش", "d023 | Metformin: Drug information | Adverse Reactions | درجه: 2"),
        ("محرمانگی", "این فایل عنوان‌های UpToDate را دارد؛ آن را منتشر یا وارد مخزن نکنید."),
        ("تعداد", f"{counts[0]} سؤال، {counts[1]} نامزد مقاله، {counts[2]} نامزد بخش"),
    ]
    for label, value in lines:
        ws.append([label, value])
    for row in ws.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=cell.column == 1)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(name=FONT, bold=True, size=14)


def progress_sheet(wb, rows):
    ws = wb.create_sheet("پیشرفت")
    ws.sheet_view.rightToLeft = True
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 14
    q, a, s = rows
    data = [
        ("مورد", "مقدار"),
        ("سؤال‌ها", f"=COUNTA('سؤال'!A2:A{q})"),
        ("سؤال‌های بررسی‌شده", f"=COUNTA('سؤال'!G2:G{q})"),
        ("نامزدهای مقاله", f"=COUNTA('مقاله'!E2:E{a})"),
        ("نامزدهای مقالهٔ داوری‌شده", f"=COUNTA('مقاله'!H2:H{a})"),
        ("درصد داوری مقاله", "=IF(B4=0,0,B5/B4)"),
        ("نامزدهای بخش", f"=COUNTA('بخش'!D2:D{s})"),
        ("نامزدهای بخش داوری‌شده", f"=COUNTA('بخش'!F2:F{s})"),
        ("درصد داوری بخش", "=IF(B7=0,0,B8/B7)"),
    ]
    for line in data:
        ws.append(line)
    for row in ws.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=cell.row == 1)
    ws["B6"].number_format = ws["B9"].number_format = "0%"


def hidden_template(path):
    wb = Workbook()
    guide = wb.active
    guide.title = "راهنما"
    guide.sheet_view.rightToLeft = True
    guide.column_dimensions["A"].width = 26
    guide.column_dimensions["B"].width = 90
    for line in (
        ("سؤال‌های آزمون پنهان — فقط مالک پروژه", ""),
        ("هدف", "سنجش نهایی هر فاز روی سؤال‌هایی که دستیار هرگز ندیده است."),
        ("چه بنویسید", "حدود ۵۰ سؤال، همان‌طور که کاربر واقعی تایپ می‌کند؛ از همهٔ دسته‌ها. سؤال‌های برگهٔ توسعه را تکرار نکنید."),
        ("جواب درست", "عنوان دقیق مقاله را از اپ کپی کنید؛ برای سؤال بخشی، عنوان بخش را هم بنویسید."),
        ("سلول‌های قابل ویرایش", "همهٔ ستون‌های برگهٔ «سؤال» به‌جز شناسه."),
        ("مثال", "h001 | دوز کلاریترومایسین در نارسایی کلیه | drug_topic | بخش | "
                 "Clarithromycin: Drug information | Dosing: Kidney Impairment: Adult"),
        ("محرمانگی", "این فایل را به دستیار نشان ندهید. ابزار سنجش فقط عدد تجمیعی گزارش می‌کند."),
    ):
        guide.append(line)
    for row in guide.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=cell.column == 1)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws = wb.create_sheet("سؤال")
    headers = ["شناسه", "سؤال", "دسته", "عمق مورد انتظار", "عنوان مقالهٔ درست", "عنوان بخش درست", "یادداشت"]
    editable = style_sheet(ws, headers, (9, 40, 16, 22, 45, 40, 30), headers[1:])
    for index in range(1, 61):
        ws.append([f"h{index:03d}", "", "", "", "", "", ""])
    finish_rows(ws, editable, 1)
    add_list(ws, CATEGORIES, "C", 61)
    add_list(ws, ("مقاله", "بخش", "پاراگراف", "تداخل", "مبهم"), "D", 61)
    path.parent.mkdir(mode=0o700, exist_ok=True)
    wb.save(path)
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--queries", type=Path, default=Path(__file__).with_name("dev-queries.csv"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--judged", type=Path, default=Path(__file__).with_name("dev-judgments.csv"),
                        help="skip candidates of levels already judged for a query")
    parser.add_argument("--round", type=int, default=1, help="judging round; >1 adds -rN to file names")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT):
        parser.error("The workbook holds UpToDate titles; choose a directory outside the repository")
    today = date.today().isoformat()
    suffix = f"-r{args.round}" if args.round > 1 else ""
    workbook_path = out / f"judging-dev-{today}{suffix}.xlsx"
    provenance_path = out / f"pool-provenance-dev-{today}{suffix}.csv"
    judged = set()
    if args.judged.exists():
        judged = {(r["query_id"], r["level"]) for r in csv.DictReader(args.judged.open(encoding="utf-8"))}
    if workbook_path.exists() or provenance_path.exists():
        parser.error(f"{workbook_path.name} already exists; remove it or build on another day")
    out.mkdir(mode=0o700, parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.queries.open(encoding="utf-8")))
    search = sqlite3.connect((args.source / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
    with SQLiteHierarchySource(args.source) as source:
        engine = HierarchicalRetriever(source.catalog, source.load_article)
        wb = Workbook()
        questions = wb.create_sheet("سؤال")
        q_headers = ["شناسه", "سؤال", "زبان", "دسته", "عمق مورد انتظار", "جزئیات",
                     "نگه‌داری؟", "عمق درست است؟", "متن بازنویسی‌شده", "یادداشت"]
        q_edit = style_sheet(questions, q_headers, (8, 40, 7, 15, 24, 22, 12, 13, 36, 30), q_headers[6:])
        articles = wb.create_sheet("مقاله")
        a_headers = ["شناسه", "سؤال", "عمق مورد انتظار", "ردیف", "شناسهٔ مقاله", "عنوان مقاله",
                     "نوع مقاله", "درجه", "یادداشت"]
        a_edit = style_sheet(articles, a_headers, (8, 34, 16, 6, 11, 60, 18, 8, 34), ("درجه", "یادداشت"))
        sections = wb.create_sheet("بخش")
        s_headers = ["شناسه", "سؤال", "مقاله", "شناسهٔ بخش", "مسیر بخش", "درجه", "یادداشت"]
        s_edit = style_sheet(sections, s_headers, (8, 34, 40, 12, 60, 8, 34), ("درجه", "یادداشت"))
        provenance = []

        for row in rows:
            questions.append([row["query_id"], row["query"], row["language"], row["category"],
                              LEVELS[row["expected_level"]], row["detail"], "", "", "", ""])
            if row["expected_level"] == "lexicomp":
                continue
            pooled, baseline_sections = pool(source, search, engine, row)
            primary = next(iter(pooled), None)
            order = list(pooled)
            random.Random(int(hashlib.sha256(row["query_id"].encode()).hexdigest()[:8], 16)).shuffle(order)
            if (row["query_id"], "article") in judged:
                order = []
            for rank, article_id in enumerate(order, 1):
                metadata = source.metadata[article_id]
                articles.append([row["query_id"], row["query"], LEVELS[row["expected_level"]], rank,
                                 article_id, metadata.title, KINDS[metadata.kind], None, ""])
                provenance.append({"query_id": row["query_id"], "article_id": article_id,
                                   "sources": " ".join(pooled[article_id])})
            if (row["expected_level"] in {"section", "paragraph"} and primary
                    and (row["query_id"], "section") not in judged):
                candidates, note = section_candidates(source, primary, row["section_keys"],
                                                      baseline_sections.get(primary, ()))
                for section in candidates:
                    sections.append([row["query_id"], row["query"], source.metadata[primary].title,
                                     section.section_id, " > ".join(section.path_titles), None, note])

        del wb["Sheet"]
        for ws, editable in ((questions, q_edit), (articles, a_edit), (sections, s_edit)):
            finish_rows(ws, editable, 1)
        add_list(questions, ("بله", "حذف", "بازنویسی"), "G", questions.max_row)
        add_list(questions, ("بله", "خیر"), "H", questions.max_row)
        add_list(articles, ("2", "1", "0"), "H", articles.max_row)
        add_list(sections, ("2", "1", "0"), "F", sections.max_row)
        guide_sheet(wb, today, (len(rows), articles.max_row - 1, sections.max_row - 1))
        progress_sheet(wb, (questions.max_row, articles.max_row, sections.max_row))
        wb.save(workbook_path)
    workbook_path.chmod(0o600)
    with provenance_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query_id", "article_id", "sources"])
        writer.writeheader()
        writer.writerows(provenance)
    provenance_path.chmod(0o600)
    template = out / "hidden" / "hidden-queries-template.xlsx"
    if not template.exists():
        hidden_template(template)
    print(f"{workbook_path}\n{len(rows)} queries, {articles.max_row - 1} article candidates, "
          f"{sections.max_row - 1} section candidates")


if __name__ == "__main__":
    main()
