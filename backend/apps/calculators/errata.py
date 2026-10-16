"""Known mistakes in the source calculators' formulas, corrected at the data.

Both importers run `fix_results` on every calculator they write, and the data
migration that introduced this ran it over the rows already there, so a
re-import from the source database does not bring a mistake back. A fix only
applies where its old text is present, so running it twice is harmless.

Each entry: calculator slug -> result position -> either (text in the source,
text it should be) or a function that returns the corrected formula. Add a
row here, with why, when another one turns up.
"""

import re


def _shift_results_down(formula):
    """`$result1/2/3` -> `$result0/1/2`. Only while the formula still reads
    `$result3`, which a corrected one never does, so it is applied once."""
    if "$result3" not in formula:
        return formula
    return re.sub(r"\$result([123])(?!\d)", lambda m: f"$result{int(m.group(1)) - 1}", formula)


FORMULA_ERRATA = {
    # The score adds `$0 + $1 + $3 ... $7 + $8`. There is no question 8 and
    # the "surgery or lower-limb fracture" question ($2, 2 points) is left
    # out, so the sum is always NaN and the calculator shows nothing.
    "revised-geneva-clinical-prediction-rule-for-pulmonary-embolism-676": {
        0: ("results += $8;", "results += $2;"),
    },
    # The ten AUDIT items are questions 0-9, but the score adds `$1 .. $10`:
    # it drops the first item and reads a question that does not exist ("$10"
    # is read as "$1" followed by a 0), so every score came out wrong.
    "alcohol-use-disorders-identification-test-audit-474": {
        0: (
            "results += $1 +$2 +$3 + $4 + $5 + $6 + $7 + $8 + $9 + $10;",
            "results += $0 + $1 + $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9;",
        ),
    },
    # The three projection rows (2 years, 1 year, 6 months) read the
    # mortality, stroke and bleeding values as `$result1 .. $result3`, but
    # those are rows 0, 1 and 2 (row 3 is the row itself). One off, so they
    # never produced anything.
    "garfield-af-risk-calculator-685": {
        3: _shift_results_down,
        4: _shift_results_down,
        5: _shift_results_down,
    },
}


def fix_results(slug, results):
    """`results` (the list stored on a calculator) with the known formula
    mistakes for `slug` corrected. Returns a new list; the input is untouched."""
    fixes = FORMULA_ERRATA.get(slug)
    if not fixes:
        return results
    out = []
    for row in results:
        fix = fixes.get(row.get("position"))
        formula = row.get("formula") or ""
        if callable(fix):
            fixed = fix(formula)
            if fixed != formula:
                row = {**row, "formula": fixed}
        elif fix and fix[0] in formula:
            row = {**row, "formula": formula.replace(fix[0], fix[1])}
        out.append(row)
    return out
