"""Extracts each drug's flashcard facts from its clinical-profile summaries --
the work build_flashcards persists as FlashcardFact rows.

Sources, per section (apps.flashcards.sections):

* indication     <- indications_and_usage
* adr_common     <- adverse_reactions, the items grouped or labelled "common"
* adr_serious    <- adverse_reactions, the items grouped or labelled
                    "important / serious / severe"
* dosage_forms   <- dosage_forms_and_strengths
* contra_boxed   <- boxed_warning first, then contraindications

The adverse-reactions summaries already separate common from serious items:
either a heading line ("عوارض شایع:") followed by bullets, or a label on
the bullet itself ("- شایع: ..."). Only those two groups are kept; items
under any other group (rare, less common) or under no group at all are left
out rather than guessed into one.
"""

import re
from collections import defaultdict

from apps.drugs.management.commands.clean_profile_boilerplate import is_null_placeholder
from apps.drugs.models import IngredientProfileSection
from apps.quiz.bank_facts import BULLET_RE, extract_facts, split_label

from .sections import SECTION_KEYS

MIN_FACT_LEN = 10

SIMPLE_SOURCES = {
    "indication": ["indications_and_usage"],
    "dosage_forms": ["dosage_forms_and_strengths"],
    "contra_boxed": ["boxed_warning", "contraindications"],
}
ADR_FIELD = "adverse_reactions"
SOURCE_FIELDS = [f for fields in SIMPLE_SOURCES.values() for f in fields] + [ADR_FIELD]

_SERIOUS_RE = re.compile(
    r"جدی|مهم|شدید|خطرناک|تهدید|serious|severe|important|life[- ]threatening", re.I
)
_OTHER_FREQ_RE = re.compile(
    r"کمتر\s*شایع|ناشایع|غیر\s*شایع|نادر|less\s+common|uncommon|infrequent|rare", re.I
)
_COMMON_RE = re.compile(r"شایع|common|frequent", re.I)
# A heading is a short line that is nothing but a name and a colon.
_HEADING_RE = re.compile(r"^[*_\s]*([^:：]{1,60}?)[*_\s]*[:：]\s*$")
# Words a group name is made of. A heading or label counts as a *group* only
# if it is built from these alone ("عوارض شایع", "مهم و جدی", "Serious
# adverse reactions"), never when it names a thing ("واکنش‌های پوستی شدید"),
# which stays the fact's own label.
_GROUP_WORDS = {
    "عوارض", "عارضه", "جانبی", "های", "شایع", "شایعتر", "شایع‌تر", "مهم", "جدی", "شدید",
    "خطرناک", "تهدیدکننده", "حیات", "نادر", "کمتر", "ناشایع", "غیرشایع", "و", "یا",
    "common", "most", "very", "serious", "severe", "important", "life-threatening",
    "rare", "less", "uncommon", "infrequent", "frequent", "side", "effects", "adverse",
    "reactions", "events", "and", "or",
}
_GROUP_WORDS_NORM = {w.replace("\u200c", "") for w in _GROUP_WORDS}


def group_of(name: str) -> tuple[bool, str | None]:
    """(is this a group name at all, which ADR section it selects or None)."""
    words = re.sub(r"\([^)]*\)", " ", name)
    words = [w for w in re.split(r"[\s/،,\-]+", words.strip().lower()) if w]
    if not words or any(w.replace("\u200c", "") not in _GROUP_WORDS_NORM for w in words):
        return False, None
    if _SERIOUS_RE.search(name):
        return True, "adr_serious"
    if _OTHER_FREQ_RE.search(name):
        return True, None
    if _COMMON_RE.search(name):
        return True, "adr_common"
    return False, None


def _usable(text: str) -> bool:
    return len(text) >= MIN_FACT_LEN and not is_null_placeholder(text)


def _fact_text(label: str | None, text: str) -> str:
    return f"{label}: {text}" if label else text


def adr_facts(summary: str) -> dict[str, list[str]]:
    """{"adr_common": [...], "adr_serious": [...]} from one adverse-reactions
    summary."""
    out: dict[str, list[str]] = {"adr_common": [], "adr_serious": []}
    group: str | None = None
    for raw in summary.split("\n"):
        line = raw.strip()
        if not line:
            continue
        bullet = BULLET_RE.match(line)
        body = bullet.group(1).strip() if bullet else line

        heading = _HEADING_RE.match(body)
        if heading:
            is_group, which = group_of(heading.group(1))
            if is_group:
                # Switches the group for the lines after it -- also to none
                # for rare / less common, so those are skipped. Any other
                # heading (an organ system, say) keeps the current group.
                group = which
            continue

        label, text = split_label(body)
        if label:
            is_group, which = group_of(label)
            if is_group:
                # "- شایع: ..." names its own group; the section heading
                # already says it, so the label is dropped from the fact.
                if which and _usable(text):
                    out[which].append(text)
                continue
        if group:
            fact = _fact_text(label, text)
            if _usable(fact):
                out[group].append(fact)
    return out


def simple_facts(summary: str) -> list[str]:
    return [
        text for f in extract_facts(summary)
        if _usable(text := _fact_text(f["label"], f["text"]))
    ]


def facts_for_ingredient(sections: dict[str, str]) -> dict[str, list[str]]:
    """field -> summary  =>  section -> [fact, ...] (deduplicated, source order)."""
    found: dict[str, list[str]] = defaultdict(list)
    for section, fields in SIMPLE_SOURCES.items():
        for field in fields:
            found[section].extend(simple_facts(sections.get(field, "")))
    for section, facts in adr_facts(sections.get(ADR_FIELD, "")).items():
        found[section].extend(facts)
    return {
        key: list(dict.fromkeys(found[key]))
        for key in SECTION_KEYS
        if found.get(key)
    }


def build_fact_rows(limit: int | None = None):
    """Unsaved FlashcardFact rows for every ingredient, plus per-section counts
    of the Persian facts (for the command's report)."""
    from .models import FlashcardFact

    summaries: dict[int, dict[str, dict[str, str]]] = defaultdict(lambda: {"fa": {}, "en": {}})
    rows_qs = (
        IngredientProfileSection.objects.filter(field__in=SOURCE_FIELDS)
        .values_list("ingredient_id", "field", "summary_fa", "summary_en")
        .order_by("ingredient_id")
    )
    for ing_id, field, fa, en in rows_qs.iterator():
        summaries[ing_id]["fa"][field] = fa or ""
        summaries[ing_id]["en"][field] = en or ""

    ingredient_ids = sorted(summaries)
    if limit:
        ingredient_ids = ingredient_ids[:limit]

    rows = []
    counts = {key: 0 for key in SECTION_KEYS}
    drugs_with_facts = 0
    for ing_id in ingredient_ids:
        any_fa = False
        for lang in ("fa", "en"):
            for section, facts in facts_for_ingredient(summaries[ing_id][lang]).items():
                for order, text in enumerate(facts):
                    rows.append(FlashcardFact(
                        ingredient_id=ing_id, section=section, lang=lang, order=order, text=text,
                    ))
                if lang == "fa":
                    counts[section] += len(facts)
                    any_fa = True
        drugs_with_facts += any_fa
    return rows, {"by_section": counts, "drugs": drugs_with_facts}
