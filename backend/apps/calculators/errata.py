"""Known mistakes in the source calculators' formulas, corrected at the data.

Calculators are identified by their source id (`Calculator.calculator_id`, the
number at the end of the slug), not by slug: the slug carries the name, and a
renamed calculator in the source must not lose its correction.

Both importers run `fix_results` on every calculator they write, and the data
migration that introduced this ran it over the rows already there, so a
re-import from the source database does not bring a mistake back. A fix only
applies where its old text is present, so running it twice is harmless.

Each entry: calculator id -> result position -> either (text in the source,
text it should be) or a function that returns the corrected formula. Add a
row here, with why, when another one turns up.
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
        formula = row.get("formula") or ""
        if callable(fix):
            row = fix(row)
        elif fix and fix[0] in formula:
            row = {**row, "formula": formula.replace(fix[0], fix[1])}
        out.append(row)
    return out


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


def fix_questions(calculator_id, questions):
    """`questions` with the units named in the titles that lack them. Returns a
    new list; the input is untouched, and a second run changes nothing."""
    fixes = QUESTION_UNITS.get(str(calculator_id))
    if not fixes:
        return questions
    out = []
    for q in questions:
        pair = fixes.get(q.get("position"))
        if pair:
            q = {**q, "title": _with_unit(q.get("title"), pair[0]), "title_fa": _with_unit(q.get("title_fa"), pair[1])}
        out.append(q)
    return out
