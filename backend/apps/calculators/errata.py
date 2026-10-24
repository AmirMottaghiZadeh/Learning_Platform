"""Known mistakes in the source calculators' formulas, corrected at the data.

Calculators are identified by their source id (`Calculator.calculator_id`, the
number at the end of the slug), not by slug: the slug carries the name, and a
renamed calculator in the source must not lose its correction.

Both importers run `fix_results` on every calculator they write, and the data
migration that introduced this ran it over the rows already there, so a
re-import from the source database does not bring a mistake back. A fix only
applies where its old text is present, so running it twice is harmless.

Each entry: calculator id -> result position -> (text in the source, text it
should be), a list of such pairs, or a function that returns the corrected
row. Add a row here, with why, when another one turns up.
"""

import re

_RESULT_TOKEN = re.compile(r"\$result(\d+)(?!\d)")
_REF_FIELDS = ("formula", "condition_formula", "title_formula", "sub_title_formula", "answer", "answer_fa")

# Calculators whose source numbers its results from 1: the first row's answer
# is `$result1`, the next `$result2`, and later formulas read them the same
# way. The app (like the other calculators) reads `$resultN` as the row at
# position N, so these formulas read the wrong row, or the row itself, and
# showed nothing or a wrong number.
ONE_BASED_RESULTS = {
    "685",
    "713",
    "890",
    "603",
    "503",
}


def _stage_names_without_prefix(row):
    """`== "Stage III"` -> `== "III"` in the formula and its condition."""
    fix = lambda text: re.sub(r'(==\s*)"Stage ', r'\1"', text or "")
    return {**row, "formula": fix(row.get("formula")), "condition_formula": fix(row.get("condition_formula"))}


def _title_formula_as_result(row):
    """A row whose whole logic sits in `title_formula` (a computed heading),
    with no formula or answer of its own: the app never runs title formulas,
    so the calculator showed nothing at all. Its text becomes the row's
    result instead."""
    if (row.get("formula") or "").strip() or not (row.get("title_formula") or "").strip():
        return row
    return {**row, "formula": row["title_formula"], "answer": "$result0", "answer_fa": "$result0"}


_ROSIER_HYPOGLYCAEMIA = "Treat hypoglycemia first (blood glucose &lt; 3.5 mmol/L) and reassess once blood glucose is normal."
_STARRT_TOO_YOUNG_OR_NOT_ICU = "Not eligible: the patient must be over 18 years old and admitted to the ICU"
_STARRT_EXCLUDED = "Not eligible: the patient meets an exclusion criterion"


FORMULA_ERRATA = {
    # The score adds `$0 + $1 + $3 ... $7 + $8`. There is no question 8 and
    # the "surgery or lower-limb fracture" question ($2, 2 points) is left
    # out, so the sum is always NaN and the calculator shows nothing.
    "676": {
        0: ("results += $8;", "results += $2;"),
    },
    # The ten AUDIT items are questions 0-9, but the score adds `$1 .. $10`:
    # it drops the first item and reads a question that does not exist ("$10"
    # is read as "$1" followed by a 0), so every score came out wrong.
    # The stage row answers "I", "II", "III" or "IV", but the survival row (and
    # the condition that shows it) compare it with "Stage I" ... "Stage IV",
    # so the survival rates were never shown.
    "573": {2: _stage_names_without_prefix},
    "474": {
        0: (
            "results += $1 +$2 +$3 + $4 + $5 + $6 + $7 + $8 + $9 + $10;",
            "results += $0 + $1 + $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9;",
        ),
    },
    # ROSIER: the score is the five deficits (face, arm, leg, speech, visual
    # field) less loss of consciousness and seizure. The visual-field item
    # ($7) was left out of the sum (and its "Yes" weighed 0, see
    # CHOICE_FACTORS), and the blood-glucose check ($0) was added as a
    # point; in the published scale a glucose below 3.5 mmol/L is treated
    # first and the patient reassessed, it is not part of the score.
    "457": {
        0: [
            (
                "var result = 0;\r\n\t\tresult += $0;\r\n\t\tresult += $1;",
                f'if ($0 == 1) {{ return "{_ROSIER_HYPOGLYCAEMIA}"; }}\r\n\t\tvar result = 0;\r\n\t\tresult += $1;',
            ),
            (
                "result += $6;\r\n       \r\n\t\tif (result > 0)",
                "result += $6;\r\n       result += $7;\r\n       \r\n\t\tif (result > 0)",
            ),
        ],
    },
    # Brain-metastases GPA: the variables read the wrong questions -- the
    # tumour type from the breast-subtype question ($5), the age from the
    # tumour type ($0), the subtype from the age ($4) -- so the tumour type
    # never changed the score and every patient scored as under 50.
    "357": {
        0: (
            "var tumor = $5;\r\n  var kps = $1;\r\n  var ecm = $2;\r\n  var number = $3;\r\n  var age = $0;\r\n  var subtype = $4;",
            "var tumor = $0;\r\n  var kps = $1;\r\n  var ecm = $2;\r\n  var number = $3;\r\n  var age = $4;\r\n  var subtype = $5;",
        ),
        1: ("var tumor = $5;", "var tumor = $0;"),
    },
    # Respiratory adverse events after vascular surgery: the age was read
    # from the dialysis question ($2) and then added to the score as a raw
    # number ($3: a 70-year-old got 70 points), dialysis from the operation
    # type ($10), and the operation type's points were never added.
    "325": {
        0: [
            ("var age = $2;", "var age = $3;"),
            ("var ondialysis = $10;", "var ondialysis = $2;"),
            (
                "results = bmivalue + gfrvalue + agevalue + $3 + $4 + $5 + $6 + $7 + $8 + $9;",
                "results = bmivalue + gfrvalue + agevalue + $4 + $5 + $6 + $7 + $8 + $9 + $10;",
            ),
        ],
    },
    # Serious renal dysfunction post-PCI: the priority choices already carry
    # their coefficients (0, 0.9566, 1.1880), but the formula then looked for
    # 2 and 3 and set everything else to 0, so urgent and emergent PCI added
    # nothing to the risk.
    "371": {
        0: (
            "if (priority == 3) {\r\n    priority = 1.1880;\r\n  } else if (priority == 2) {\r\n    priority = 0.9566;\r\n  } else priority = 0;",
            "",
        ),
    },
    # IPSS: the quality-of-life row returned question 7 (nocturia, $6) instead
    # of the quality-of-life question ($7), whose answer was never used.
    "338": {
        2: ("var qol = $6;", "var qol = $7;"),
    },
    # MSA: a sporadic, progressive, adult-onset disorder ($0) is required for
    # both possible and probable MSA, but was never read -- "No" there still
    # gave "Probable MSA".
    "563": {
        0: (
            "(function() {\r\n\r\nvar resultsA = 0;",
            '(function() {\r\n\r\nif ($0 == 0) {\r\nreturn "MSA not likely";\r\n}\r\n\r\nvar resultsA = 0;',
        ),
    },
    # STARRT-AKI: the inclusion question ($0: over 18 and in the ICU) and the
    # exclusion criteria ($8) were read but never used, so an excluded patient
    # was "Fully eligible"; a creatinine under the minimum returned nothing.
    "362": {
        0: (
            "\r\n\r\nif ((minimumcreatinine === true) && (twofoldcreatinine === false",
            f'\r\n\r\nif (ageICU == 0) {{\r\nreturn "{_STARRT_TOO_YOUNG_OR_NOT_ICU}";\r\n}}\r\n'
            f'if (exclusion == 1) {{\r\nreturn "{_STARRT_EXCLUDED}";\r\n}}\r\n'
            'if (minimumcreatinine === false) {\r\nreturn "Not eligible at present; reassess at next screen";\r\n}\r\n'
            "if ((minimumcreatinine === true) && (twofoldcreatinine === false",
        ),
    },
    # Contrast nephropathy (Mehran): anaemia is a haematocrit under 39% in men
    # and under 36% in women, but the formula took the "Female" answer (0) for
    # male, so each sex was held to the other's threshold.
    "47": {
        0: ("if (gender == 0.0) { //male", "if (gender == 1) { //male"),
    },
    # MATCH-D (home haemodialysis and home PD): all of the logic is a title
    # formula, which the app does not run.
    "136": {0: _title_formula_as_result},
    "137": {0: _title_formula_as_result},
}

# Choices whose weight in the source is wrong, found by their title (not their
# index, which a choice added below would shift).
#   calculator id -> question position -> choice title -> (weight in the source, weight it should be)
CHOICE_FACTORS = {
    # ROSIER: a new visual-field defect scores +1; both answers weighed 0.
    "457": {7: {"Yes": ("0", "1")}},
    # IPSS for Waldenström macroglobulinaemia: a beta-2-microglobulin above
    # 3 mg/L scores 1; both answers weighed 0.
    "610": {3: {">3 mg/L": ("0", "1")}},
    # GAD-7: "Nearly every day" is 3 on every item; it was 2 on item 4 and 4 on item 5.
    "317": {3: {"Nearly every day": ("2", "3")}, 4: {"Nearly every day": ("4", "3")}},
    # NIHSS: an amputated or fused limb is untestable and scores 0, as on the
    # other three limbs; on the right arm it added 5.
    "273": {7: {"Amputation or joint fusion": ("5", "0")}},
    # IIEF-5: "(2) A few times" scores 2, as on the other items; here it was 0.
    "377": {1: {"(2)  A few times (much less than half the time)": ("0", "2")}},
    # IPSS: on intermittency "About half the time" is 3 (with the missing
    # "Less than half the time" as 2, see MISSING_CHOICES), as on the other items.
    "338": {2: {"About half the time": ("2", "3")}},
}

# Choices the source left out: calculator id -> question position -> (index
# to insert at, the choice). Added only while no choice has that title.
MISSING_CHOICES = {
    "338": {
        2: (
            2,
            {
                "answer_factor": "2",
                "title_primary": "Less than half the time",
                "title_secondary": "",
                "title_primary_fa": "کمتر از نیمی از موارد",
                "title_secondary_fa": None,
            },
        ),
    },
}

# Persian for the English text a corrected formula now returns (see
# `formula_strings_fa`): calculator id -> English -> Persian.
STRINGS_FA = {
    "457": {_ROSIER_HYPOGLYCAEMIA: "ابتدا هیپوگلیسمی را درمان کنید (قند خون کمتر از 3.5 mmol/L) و پس از طبیعی شدن قند خون دوباره ارزیابی کنید."},
    "362": {
        _STARRT_TOO_YOUNG_OR_NOT_ICU: "واجد شرایط نیست: بیمار باید بالای 18 سال و بستری در ICU باشد",
        _STARRT_EXCLUDED: "واجد شرایط نیست: بیمار یکی از معیارهای خروج را دارد",
    },
}


def renumber_from_one(results):
    """`$resultN` -> `$result(N-1)` in every formula and answer. Applied only
    while the first row's answer is still `$result1`, which it no longer is
    once renumbered, so a second run changes nothing."""
    if not results or (results[0].get("answer") or "").strip() != "$result1":
        return results
    shift = lambda text: _RESULT_TOKEN.sub(lambda m: f"$result{max(int(m.group(1)) - 1, 0)}", text)
    out = []
    for row in results:
        row = dict(row)
        for field in _REF_FIELDS:
            if row.get(field):
                row[field] = shift(row[field])
        out.append(row)
    return out


def fix_results(calculator_id, results):
    """`results` (the list stored on a calculator) with the known mistakes
    for the calculator with this source id corrected. Returns a new list; the input is untouched."""
    calculator_id = str(calculator_id)
    if calculator_id in ONE_BASED_RESULTS:
        results = renumber_from_one(results)
    fixes = FORMULA_ERRATA.get(calculator_id)
    if not fixes:
        return results
    out = []
    for row in results:
        fix = fixes.get(row.get("position"))
        if callable(fix):
            row = fix(row)
        elif fix:
            for old, new in [fix] if isinstance(fix, tuple) else fix:
                formula = row.get("formula") or ""
                if old in formula:
                    row = {**row, "formula": formula.replace(old, new)}
        out.append(row)
    return out


def fix_strings_fa(calculator_id, strings):
    """`formula_strings_fa` with the Persian for text added by a corrected
    formula. Returns a new dict; the input is untouched."""
    extra = STRINGS_FA.get(str(calculator_id))
    if not extra:
        return strings
    return {**(strings or {}), **extra}


# A multiple-choice question whose choices are bare numbers or ranges ("<50",
# "120-129") says what is measured but not in what unit, so the learner is
# asked for "Age?" or "CrCl?" with nothing to say how it is counted. The unit
# is added to the question's title, in English and in Persian.
#   calculator id -> question position -> (unit, Persian unit)
QUESTION_UNITS = {
    "286": {1: ("years", "سال")},
    "451": {0: ("years", "سال")},
    "489": {1: ("years", "سال")},
    "731": {0: ("years", "سال")},
    "272": {2: ("years", "سال")},
    "536": {0: ("years", "سال")},
    "252": {1: ("years", "سال")},
    "253": {1: ("years", "سال")},
    "98": {1: ("years", "سال")},
    "99": {1: ("years", "سال")},
    "114": {4: ("years", "سال")},
    "469": {0: ("years", "سال")},
    "284": {0: ("years", "سال")},
    "675": {4: ("kg/m²", "kg/m²")},
    "45": {2: ("×10⁹/L", "×10⁹/L")},
    "113": {1: ("×10⁹/L", "×10⁹/L")},
    "268": {2: ("×10³/µL", "×10³/µL")},
    "72": {1: ("U/L", "U/L")},
    "190": {3: ("U/L", "U/L"), 4: ("U/L", "U/L")},
    "53": {1: ("mL/min", "mL/min")},
    "841": {1: ("mL/min/1.73 m²", "mL/min/1.73 m²")},
    "530": {0: ("beats/min", "ضربان در دقیقه")},
    "676": {1: ("beats/min", "ضربان در دقیقه")},
    "376": {0: ("mmHg", "mmHg")},
}


def _with_unit(title, unit):
    """`Age?` -> `Age (years)?`; `Resting pulse rate` -> `Resting pulse rate (beats/min)`.
    A title that already carries the unit in brackets is left as it is."""
    if not title or f"({unit})" in title:
        return title
    m = re.search(r"\s*[?؟]", title) or re.search(r"\s*:\s*$", title)
    if m:
        return f"{title[: m.start()]} ({unit}){title[m.start():].lstrip()}"
    return f"{title} ({unit})"


def _with_choices(question, factors, missing):
    """`question` with the choice weights in `factors` (title -> (old, new))
    corrected, each only while it still has its old value, and the `missing`
    choice (index, choice) added unless one with its title is there."""
    choices = list(question.get("choices") or [])
    title = lambda choice: (choice.get("title_primary") or "").strip()
    for i, choice in enumerate(choices):
        old, new = (factors or {}).get(title(choice), (None, None))
        if old is not None and (choice.get("answer_factor") or "").strip() == old:
            choices[i] = {**choice, "answer_factor": new}
    if missing and not any(title(c) == title(missing[1]) for c in choices):
        choices.insert(missing[0], dict(missing[1]))
    return {**question, "choices": choices}


def fix_questions(calculator_id, questions):
    """`questions` with the units named in the titles that lack them and the
    wrong or missing choices corrected. Returns a new list; the input is
    untouched, and a second run changes nothing."""
    units = QUESTION_UNITS.get(str(calculator_id))
    factors = CHOICE_FACTORS.get(str(calculator_id))
    missing = MISSING_CHOICES.get(str(calculator_id))
    if not units and not factors and not missing:
        return questions
    out = []
    for q in questions:
        position = q.get("position")
        pair = (units or {}).get(position)
        if pair:
            q = {**q, "title": _with_unit(q.get("title"), pair[0]), "title_fa": _with_unit(q.get("title_fa"), pair[1])}
        if (factors or {}).get(position) or (missing or {}).get(position):
            q = _with_choices(q, (factors or {}).get(position), (missing or {}).get(position))
        out.append(q)
    return out
