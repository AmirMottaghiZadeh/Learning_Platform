#!/usr/bin/env python3
"""Build the phase-1 lexicon review workbook (private: it shows UpToDate titles).

Each row is one proposal. The reviewer marks only wrong rows ("خیر") and
writes the correction; a blank row is accepted.

    python3 docs/search/eval/build_lexicon_review.py \
        --source /home/amir/Documents/UpToDate \
        --output-dir /home/amir/Documents/pharmenta-search-eval
"""

import argparse
import csv
from datetime import date
from pathlib import Path
import sqlite3
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[3]
LEXICON = ROOT / "backend" / "apps" / "uptodate" / "search_lexicon"
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_concepts import normalize  # noqa: E402

FONT = "Arial"
HEAD_FILL = PatternFill("solid", start_color="D9E2F3")
EDIT_FILL = PatternFill("solid", start_color="FFF2CC")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
ROLES = {"intent": "هدف سؤال", "context": "زمینه", "population": "جمعیت", "route": "روش مصرف",
         "form": "شکل دارویی (فقط اشاره)", "stop": "کلمهٔ بی‌اهمیت (نادیده گرفته می‌شود)"}
MEANING = {
    "dosing": "دوز و تنظیم دوز", "adverse": "عوارض جانبی دارو", "interaction": "تداخل دارویی",
    "food_interaction": "تداخل با غذا", "mechanism": "مکانیسم اثر", "pharmacokinetics": "فارماکوکینتیک",
    "administration": "نحوهٔ مصرف و آماده‌سازی", "dosage_forms": "اشکال دارویی", "indications": "موارد مصرف",
    "contraindications": "منع مصرف", "warnings": "هشدارها و احتیاط‌ها", "monitoring": "پایش",
    "storage": "نگهداری", "brand": "نام تجاری", "price": "قیمت", "category": "دستهٔ دارویی",
    "counseling": "آموزش به بیمار", "overdose": "مسمومیت و اوردوز", "treatment": "درمان",
    "diagnosis": "تشخیص و ارزیابی", "clinical_features": "علائم و تظاهرات", "prevention": "پیشگیری",
    "screening": "غربالگری", "etiology": "علت", "prognosis": "پیش‌آگهی", "overview": "مرور کلی",
    "kidney": "نارسایی کلیه", "liver": "نارسایی کبد", "dialysis": "دیالیز", "obesity": "چاقی",
    "pregnancy": "بارداری", "lactation": "شیردهی", "acute": "حاد", "chronic": "مزمن", "severe": "شدید",
    "mild": "خفیف", "inpatient": "بستری", "outpatient": "سرپایی", "pediatric": "کودکان",
    "neonate": "نوزادان", "adolescent": "نوجوانان", "adult": "بزرگسالان", "elderly": "سالمندان",
    "iv": "وریدی", "im": "عضلانی", "sc": "زیرجلدی", "oral": "خوراکی", "bolus": "بولوس",
    "infusion": "انفوزیون", "topical": "موضعی", "inhaled": "استنشاقی", "ophthalmic": "چشمی",
    "otic": "گوشی", "rectal": "رکتال", "nasal": "بینی", "tablet": "قرص", "capsule": "کپسول",
    "syrup": "شربت و سوسپانسیون", "injection": "تزریقی", "cream": "کرم و پماد", "suppository": "شیاف",
    "inhaler": "اسپری", "question": "کلمات پرسشی", "function": "حروف اضافه و ربط", "person": "بیمار و فرد",
    "unit": "واحدها (عدد و واحد جدا خوانده می‌شود)", "generic": "کلمات عمومی",
    "complications": "عوارض بیماری", "epidemiology": "شیوع", "classification": "طبقه‌بندی و مرحله‌بندی",
    "comparison": "مقایسه", "alternative": "جایگزین", "discontinuation": "قطع دارو", "missed_dose": "دوز فراموش‌شده",
    "calculator": "ماشین‌حساب", "vaginal": "واژینال", "sublingual": "زیرزبانی", "transdermal": "چسب پوستی",
    "intrathecal": "داخل نخاعی", "extended_release": "آهسته‌رهش", "powder": "پودر و ساشه",
}
KIND_LABELS = {"condition": "بیماری/وضعیت", "symptom": "علامت", "test": "آزمایش/تصویربرداری",
               "class": "دستهٔ دارویی", "organism": "میکروب", "drug": "دارو (نام رایج در ایران)"}
POPULATIONS = {"any": "همه", "adult": "بزرگسال", "pediatric": "کودک", "neonate": "نوزاد", "elderly": "سالمند"}


def rows(name):
    with (LEXICON / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sheet(wb, title, headers, widths, data):
    ws = wb.create_sheet(title)
    ws.sheet_view.rightToLeft = True
    ws.append(headers)
    for line in data:
        ws.append(line)
    editable = {len(headers) - 1, len(headers)}
    for row in ws.iter_rows():
        for cell in row:
            header = cell.row == 1
            cell.font = Font(name=FONT, bold=header)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = THIN
            cell.fill = HEAD_FILL if header else EDIT_FILL if cell.column in editable else PatternFill()
    for index, width in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(1, index).column_letter].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    validation = DataValidation(type="list", formula1='"خیر"', allow_blank=True)
    ws.add_data_validation(validation)
    validation.add(f"{ws.cell(1, len(headers) - 1).column_letter}2:{ws.cell(1, len(headers) - 1).column_letter}{max(ws.max_row, 2)}")
    return ws


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT):
        parser.error("The workbook holds UpToDate titles; choose a directory outside the repository")
    path = out / f"lexicon-review-{date.today().isoformat()}.xlsx"
    if path.exists():
        parser.error(f"{path.name} already exists")
    search = sqlite3.connect((args.source / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
    titles = dict(search.execute("SELECT id, title FROM topic"))
    first_topic = {}
    for concept_id, hits in search.execute("SELECT id, x_topic_hits FROM query_topic"):
        first = (hits or "").split(",")[0]
        first_topic[concept_id] = titles.get(int(first), "") if first else ""
    best = {}
    for concept_id, word, weight in search.execute("SELECT id, word, weight FROM query"):
        for form in (normalize(word),):
            if weight > best.get(form, (0, None))[0]:
                best[form] = (weight, concept_id)

    wb = Workbook()
    guide = wb.active
    guide.title = "راهنما"
    guide.sheet_view.rightToLeft = True
    guide.column_dimensions["A"].width = 24
    guide.column_dimensions["B"].width = 95
    for line in (
        ("بازبینی واژه‌نامهٔ جست‌وجو — فاز ۱", ""),
        ("چه کنید", "هر ردیف یک پیشنهاد است. اگر درست است، کاری نکنید. اگر اشتباه است، ستون «اشتباه است؟» را «خیر» بزنید "
                    "و در ستون آخر اصلاح را بنویسید (مثلاً صورت فارسی بهتر، یا اینکه این واژه باید حذف شود)."),
        ("اولویت", "۱) «بیماری‌ها» ۲) «واژه‌های سؤال» ۳) «بخش‌های مونوگراف» ۴) «داروهای وصل‌نشده» (اختیاری)."),
        ("ستون «مقالهٔ اول UpToDate»", "فقط برای کمک: نشان می‌دهد این مفهوم در خود UpToDate اول به کدام مقاله می‌رسد. "
                                       "اگر نامربوط است، یعنی مفهوم انگلیسی اشتباه انتخاب شده؛ «خیر» بزنید."),
        ("صورت‌ها", "با | جدا شده‌اند. اگر صورت رایجی جا افتاده، در ستون اصلاح اضافه کنید (مثلاً «+ قرص فشار»)."),
        ("مثال", "پنومونی|ذات الریه … ← pneumonia ← اگر درست است خالی بماند."),
        ("سلول‌های قابل ویرایش", "فقط دو ستون زرد آخر هر برگه."),
        ("محرمانگی", "این فایل عنوان مقاله‌های UpToDate را دارد؛ منتشر نکنید."),
    ):
        guide.append(line)
    for row in guide.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=cell.column == 1 or cell.row == 1)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    concepts = []
    for row in rows("concepts_fa.csv"):
        weight_concept = best.get(normalize(row["en"]))
        concepts.append([row["fa"].replace("|", " | "), row["en"], KIND_LABELS[row["kind"]],
                         first_topic.get(weight_concept[1], "") if weight_concept else "", None, ""])
    sheet(wb, "بیماری‌ها", ["صورت‌های فارسی", "مفهوم انگلیسی", "نوع", "مقالهٔ اول UpToDate", "اشتباه است؟", "اصلاح / یادداشت"],
          (42, 26, 13, 55, 12, 34), concepts)
    terms = [[ROLES[r["role"]], MEANING.get(r["key"], r["key"]), r["forms"].replace("|", " | "), None, ""]
             for r in rows("terms.csv")]
    sheet(wb, "واژه‌های سؤال", ["نقش", "معنی", "صورت‌های فارسی و انگلیسی", "اشتباه است؟", "اصلاح / یادداشت"],
          (22, 22, 70, 12, 34), terms)
    sections = [[MEANING.get(r["facet"].split("+")[0], r["facet"]) + (" + " + MEANING[r["facet"].split("+")[1]] if "+" in r["facet"] else ""),
                 POPULATIONS[r["population"]], r["heading"], "اصلی" if r["rank"] == "1" else "قابل قبول", None, ""]
                for r in rows("monograph_sections.csv")]
    sheet(wb, "بخش‌های مونوگراف", ["سؤال دربارهٔ", "جمعیت", "بخش مونوگراف", "رتبه", "اشتباه است؟", "اصلاح / یادداشت"],
          (30, 12, 55, 12, 12, 34), sections)
    drugs = [[r["fa"], r["en"], "نیاز به بازبینی" if r["status"] == "needs_review" else "وصل نشد", None, ""]
             for r in rows("drugs_fa.csv") if r["status"] in {"needs_review", "unmatched"}]
    sheet(wb, "داروهای وصل‌نشده", ["نام فارسی", "نام انگلیسی پروژه", "وضعیت", "اشتباه است؟", "نام مونوگراف UpToDate یا یادداشت"],
          (34, 34, 16, 12, 40), drugs)
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    wb.save(path)
    path.chmod(0o600)
    print(f"{path}\nconditions {len(concepts)}, terms {len(terms)}, sections {len(sections)}, drugs {len(drugs)}")


if __name__ == "__main__":
    main()
