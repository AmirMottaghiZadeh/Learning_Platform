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
