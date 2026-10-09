"""One-time cleanup of non-informative boilerplate in IngredientProfileSection
summaries, per explicit user request. Runs over both `summary_fa` and
`summary_en` (the first version of this command only touched `summary_fa`):

1. Drop bullets that are just "hypersensitivity to this drug / any of the
   product's components" -- true of virtually every drug, so it never
   discriminates one drug from another and is useless as quiz material.
   Persian: scoped to short bullets (<=HYPERSENSITIVITY_MAX_LEN chars) so
   longer ones that also carry real content (e.g. named cross-reactive drug
   classes, specific infusion-reaction warnings like PERJETA/PHESGO's) are
   left untouched -- verified against the actual data before picking the
   cutoff. English: length isn't a clean signal there (plenty of long
   bullets are still pure boilerplate, just listing several drug-name
   synonyms; plenty of short ones name a real allergen) -- instead kept
   whenever a HYPERSENSITIVITY_VALUE_KEYWORDS term (a named excipient like
   "peanut" or "tartrazine", or a cross-reactive drug class like "NSAID" or
   "quinolone") is present, since that's the actual signal for "this bullet
   says something a generic one wouldn't."
2. Drop bullets whose entire content is a generic "this section has
   nothing" placeholder (e.g. "ندارد.", "منع مصرفی ذکر نشده است"). Specific
   negative facts tied to a drug/population/condition (e.g. "not approved
   for use in children", "no interaction with nelfinavir") are real,
   testable information and are deliberately left alone -- NULL_PHRASES is
   an exact-match allowlist, not a substring search, precisely so those
   don't get swept up too.
3. In `indications_and_usage` specifically (and only there -- the same
   phrasing is real, on-topic content in warnings/contraindications), drop
   bullets that are fundamentally a negative/exclusion statement ("not
   suitable for X", "not indicated for Y", "efficacy has not been evaluated
   in Z") rather than an approved use. Verified against the live bank
   generator: 69 of these had been sampled as the *correct answer* to "which
   of the following is an approved indication of X" -- backwards, since a
   "not indicated for" fact is the opposite of an indication. Persian is
   SOV, so the negative predicate sits at the END of the clause
   (NEGATIVE_INDICATION_SUFFIXES_FA, matched as a suffix); English is SVO,
   so it sits at or near the START (NEGATIVE_INDICATION_MARKERS_EN, matched
   only within the first EARLY_POSITION_MAX chars, so a line that *opens*
   with a real positive indication and only later adds a parenthetical
   caveat -- e.g. "Agitation associated with dementia ... (not indicated as
   an as-needed/'prn' treatment)" -- is correctly left alone).

Idempotent and safe to re-run; only ever drops whole lines, never rewrites
one, so it can't corrupt a sentence it decides to keep.
"""

import re

from django.core.management.base import BaseCommand

from apps.drugs.models import IngredientProfileSection

HYPERSENSITIVITY_MAX_LEN = 130

NULL_PHRASES = {
    "ندارد",
    "منع مصرفی ذکر نشده است",
    "هیچ منع مصرف مطلقی ذکر نشده است",
    "منع مصرف مطلق شناخته‌شده‌ای وجود ندارد",
    "منع مصرف شناخته‌شده‌ای وجود ندارد",
    "هیچ منع مصرف مطلقی وجود ندارد",
    "هیچ منع مصرف شناخته‌شده‌ای گزارش نشده است",
    "در برچسب هیچ منع مصرف مطلقی ذکر نشده است",
    "منع مصرفی ندارد",
    "موردی گزارش نشده است",
    "موردی ذکر نشده است",
    "موردی جداگانه گزارش نشده است",
    "موردی جداگانه دیگر گزارش نشده است",
    "هشدار و احتیاط خاصی ذکر نشده است",
    "تداخل دارویی گزارش‌شده‌ای وجود ندارد",
    "تداخل دارویی شناخته‌شده‌ای وجود ندارد",
}

# A named excipient/allergen or a cross-reactive drug class -- the actual
# "says something specific" signal for an English hypersensitivity bullet,
# verified against the real data (see module docstring).
HYPERSENSITIVITY_VALUE_KEYWORDS_EN = {
    "peanut", "soy", "soybean", "lactose", "milk", "latex", "tartrazine", "yellow no",
    "fd&c", "benzyl alcohol", "metabisulfite", "sulfite", "polysorbate", "povidone",
    "gluten", "wheat", "egg", "gelatin", "cobalt", "iodine", "sesame", "parabens",
    "sodium benzoate", "aspartame", "e. coli", "e.coli", "chinese hamster", "cho cell",
    "murine", "mouse protein", "bovine", "hamster protein", "human albumin",
    "albumin (human)", "phosphatidylcholine", "castor oil",
    "nsaid", "quinolone", "beta-lactam", "sulfonamide", "sulfa ", "azole", "beta-blocker",
    "aminosalicylate", "salicylate", "corticosteroid", "local anesthetic", "amide-type",
    "ester-based", "carbapenem", "cephalosporin", "penicillin", "rapamycin", "echinocandin",
    "aminoquinolin", "interferon", "antihistamine", "benzimidazole", "fluoroquinolone",
}

# Persian is SOV: the negative predicate is the clause's last words, so this
# is matched as a suffix (after stripping the bullet marker and trailing
# punctuation) -- see module docstring point 3.
NEGATIVE_INDICATION_SUFFIXES_FA = (
    "مناسب نیست", "مناسب نیستند", "اندیکاسیون ندارد", "اندیکاسیونی ندارد",
    "کاربرد ندارد", "بررسی نشده است", "مطالعه نشده است", "ارزیابی نشده است",
    "به کار نمی‌رود", "به کار نمی رود",
)
# One verified exception: this bullet is a genuine positive indication ("as
# a fallback when alternative treatments aren't available or suitable") --
# the negated word is the *alternative* treatment, not the drug itself, so
# it only happens to end in the same suffix.
NEGATIVE_INDICATION_PROTECTED_FA = {
    "پیشگیری از سیاه‌زخم استنشاقی هنگامی که درمان‌های جایگزین در دسترس یا مناسب نیستند",
}

# English is SVO: the negative predicate opens the clause, so this is only
# checked within the first EARLY_POSITION_MAX characters -- a line that
# leads with a real positive indication and only adds a negative caveat
# later (deep in a parenthetical) is left alone. See module docstring.
NEGATIVE_INDICATION_MARKERS_EN = (
    "not studied", "has not been studied", "has not been evaluated", "not evaluated",
    "not suitable", "not effective", "not indicated", "not approved", "not recommended",
    "no evidence of effectiveness",
)
EARLY_POSITION_MAX = 30

_LABEL_RE = re.compile(r"^([^:：]{1,40}):\s*(.*)$")
_BULLET_RE = re.compile(r"^-\s+(.*)$")


def _normalize(text):
    return text.strip().rstrip(".،؛)؛ ").strip()


def is_null_placeholder(content):
    if _normalize(content) in NULL_PHRASES:
        return True
    m = _LABEL_RE.match(content)
    if m and _normalize(m.group(2)) in NULL_PHRASES:
        return True
    return False


def is_hypersensitivity_boilerplate(content):
    return "حساسیت" in content and "اجزا" in content and len(content) <= HYPERSENSITIVITY_MAX_LEN


def is_hypersensitivity_boilerplate_en(content):
    low = content.lower()
    if "hypersensitivity" not in low:
        return False
    if "component" not in low and "ingredient" not in low:
        return False
    return not any(kw in low for kw in HYPERSENSITIVITY_VALUE_KEYWORDS_EN)


def is_negative_indication_fa(content):
    normalized = _normalize(content)
    if normalized in NEGATIVE_INDICATION_PROTECTED_FA:
        return False
    return any(normalized.endswith(suf) for suf in NEGATIVE_INDICATION_SUFFIXES_FA)


def is_negative_indication_en(content):
    low = content.lower()
    best = None
    for marker in NEGATIVE_INDICATION_MARKERS_EN:
        idx = low.find(marker)
        if idx != -1 and (best is None or idx < best):
            best = idx
    return best is not None and best <= EARLY_POSITION_MAX


def clean_text(text, field, lang):
    """Returns (cleaned_text, n_lines_removed)."""
    kept = []
    removed = 0
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _BULLET_RE.match(line)
        content = m.group(1).strip() if m else line

        drop = is_null_placeholder(content)
        if not drop:
            drop = (
                is_hypersensitivity_boilerplate(content) if lang == "fa"
                else is_hypersensitivity_boilerplate_en(content)
            )
        if not drop and field == "indications_and_usage":
            drop = (
                is_negative_indication_fa(content) if lang == "fa"
                else is_negative_indication_en(content)
            )

        if drop:
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept), removed


class Command(BaseCommand):
    help = (
        "Strip non-informative boilerplate (hypersensitivity-to-components, "
        "generic 'nothing here' placeholders, negative/exclusion statements "
        "mis-filed under indications) from drug profile summaries, fa and en."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        touched = 0
        total_removed = 0
        emptied = 0
        to_save = []
        for s in IngredientProfileSection.objects.exclude(summary_fa="", summary_en=""):
            update_fields = []
            removed_here = 0

            if s.summary_fa:
                cleaned_fa, removed_fa = clean_text(s.summary_fa, s.field, "fa")
                if removed_fa:
                    s.summary_fa = cleaned_fa
                    update_fields.append("summary_fa")
                    removed_here += removed_fa

            if s.summary_en:
                cleaned_en, removed_en = clean_text(s.summary_en, s.field, "en")
                if removed_en:
                    s.summary_en = cleaned_en
                    update_fields.append("summary_en")
                    removed_here += removed_en

            if update_fields:
                touched += 1
                total_removed += removed_here
                if not s.summary_fa.strip() and not s.summary_en.strip():
                    emptied += 1
                to_save.append((s, update_fields))

        if not dry_run and to_save:
            # bulk_update needs one shared field list; split by which fields
            # actually changed so an fa-only touch doesn't rewrite en with
            # its own (unchanged) value, and vice versa.
            for fields in ({"summary_fa"}, {"summary_en"}, {"summary_fa", "summary_en"}):
                batch = [s for s, uf in to_save if set(uf) == fields]
                if batch:
                    IngredientProfileSection.objects.bulk_update(batch, list(fields), batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"{'(dry-run) ' if dry_run else ''}{touched} sections touched, "
            f"{total_removed} boilerplate lines removed, {emptied} sections now empty"
        ))
