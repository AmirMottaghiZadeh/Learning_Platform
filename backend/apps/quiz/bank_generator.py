"""Rule-based (no LLM) MCQ generation from drug clinical-profile summaries.

Question fields are the five a learner is actually drilled on in practice --
indication, adverse reactions, warnings, absolute contraindications, and
dosing -- deliberately excluding mechanism (too abstract to quiz as a
discrete fact) and the two fields the previous version of this bank used
(dosage forms/strengths, pregnancy) that are out of scope for this one.

For each (ingredient, field), the ingredient's own facts
(apps.quiz.bank_facts.extract_facts) become candidate correct answers.
Distractors are drawn from other ingredients' facts in the same field,
biased *toward* the subject's own ATC class rather than away from it: a
distractor from an unrelated drug class can be eliminated by category alone
without knowing the actual fact, which is what makes a question easy. A
question is kept only if at least one of its three distractors shares the
subject's own ATC anatomical section (L1 code) -- otherwise it's dropped
rather than kept as an easy question. `difficulty` records how far that
went: "hard" when all three distractors share the subject's own ATC
subclass (L2 code, i.e. genuine same-class confusers), "medium" otherwise.

Target is >= 15 questions per well-documented ingredient; ingredients with
thinner source material, or too few same-class peers to clear the
medium-difficulty floor, simply get fewer -- there is no padding to a fixed
count and no distractor invented to make one up.
"""

import random
from collections import Counter, defaultdict

from apps.drugs.management.commands.clean_profile_boilerplate import is_null_placeholder
from apps.drugs.models import Ingredient, IngredientProfileSection

from .bank_facts import extract_facts

QUESTION_FIELDS = [
    "indications_and_usage",
    "adverse_reactions",
    "warnings",
    "contraindications",
    "dosage_and_administration",
]

# Max correct-answer facts drawn per (ingredient, field) -- caps any one
# field from dominating a drug's question set. Adverse reactions tends to be
# the richest field (long enumerated lists); dosing sections tend to be the
# thinnest (a handful of dense, formulation-specific bullets).
FIELD_CAP = {
    "indications_and_usage": 5,
    "adverse_reactions": 8,
    "warnings": 6,
    "contraindications": 5,
    "dosage_and_administration": 4,
}

PROMPT_TEMPLATE = {
    "indications_and_usage": "کدام مورد زیر از موارد مصرف تأییدشدهٔ «{drug}» است؟",
    "adverse_reactions": "کدام مورد زیر از عوارض جانبی گزارش‌شدهٔ «{drug}» است؟",
    "warnings": "کدام مورد زیر از هشدارهای «{drug}» است؟",
    "contraindications": "کدام مورد زیر از موارد منع مطلق مصرف «{drug}» است؟",
    "dosage_and_administration": "کدام مورد زیر دربارهٔ نحوهٔ دوز و تجویز «{drug}» صحیح است؟",
}

MIN_FACT_LEN = 10
# A fact text this common across different ingredients in the same field is
# boilerplate, not a distinguishing fact about any one of them.
MAX_GLOBAL_REPEAT = 3
DISTRACTORS_NEEDED = 3


def _fact_text(fact: dict) -> str:
    # Every field in this bank is genuinely bulleted (unlike the old bank's
    # mechanism/pregnancy fields, which were one paragraph split into
    # sentences), so a bullet's label -- when present -- is kept: it's often
    # the only part naming the specific thing the rest of the bullet just
    # quantifies or qualifies (e.g. "Aseptic meningitis: cases have been
    # reported", "Delayed-release capsule: take on an empty stomach").
    if fact["label"]:
        return f'{fact["label"]}: {fact["text"]}'
    return fact["text"]


def _is_low_quality(text: str) -> bool:
    return len(text) < MIN_FACT_LEN or is_null_placeholder(text)


def _collect_pools() -> dict[str, dict[int, list[str]]]:
    """field -> ingredient_id -> [fact text, ...], already quality-filtered
    and with corpus-wide boilerplate (near-duplicate text) dropped."""
    per_field: dict[str, dict[int, list[str]]] = {f: defaultdict(list) for f in QUESTION_FIELDS}
    text_counts: dict[str, Counter] = {f: Counter() for f in QUESTION_FIELDS}

    sections = (
        IngredientProfileSection.objects
        .filter(field__in=QUESTION_FIELDS)
        .exclude(summary_fa="")
    )
    for s in sections.iterator():
        texts = [
            t for f in extract_facts(s.summary_fa)
            if not _is_low_quality(t := _fact_text(f))
        ]
        if not texts:
            continue
        for t in texts:
            text_counts[s.field][t] += 1
        per_field[s.field][s.ingredient_id] = texts

    for field in QUESTION_FIELDS:
        counts = text_counts[field]
        for ing_id, texts in list(per_field[field].items()):
            kept = [t for t in texts if counts[t] < MAX_GLOBAL_REPEAT]
            if kept:
                per_field[field][ing_id] = kept
            else:
                del per_field[field][ing_id]
    return per_field


def _atc_maps() -> tuple[dict[int, set[str]], dict[int, set[str]]]:
    """(l1_map, l2_map): ingredient_id -> its ATC anatomical-section codes
    (1 char, e.g. "C") and its ATC subclass codes (3 chars, e.g. "C07")."""
    l1_map: dict[int, set[str]] = {}
    l2_map: dict[int, set[str]] = {}
    for ing in Ingredient.objects.prefetch_related("atc_codes"):
        codes = [c.code for c in ing.atc_codes.all()]
        l1_map[ing.id] = {c[0] for c in codes}
        l2_map[ing.id] = {c[:3] for c in codes}
    return l1_map, l2_map


def _pick_distractors(
    rng: random.Random,
    pool: dict[int, list[str]],
    own_id: int,
    own_l1: set[str],
    own_l2: set[str],
    l1_map: dict[int, set[str]],
    l2_map: dict[int, set[str]],
    correct_text: str,
) -> tuple[list[str], int, int] | None:
    """Returns (distractor_texts, same_l1_count, same_l2_count), or None if
    fewer than DISTRACTORS_NEEDED distinct usable candidates exist at all.
    Candidates sharing the subject's own ATC subclass (L2) are tried first,
    then its broader anatomical section (L1), then anything else -- so the
    three actually picked are the hardest available, not a random draw that
    happens to include some."""
    other_ids = [i for i in pool if i != own_id]
    if len(other_ids) < DISTRACTORS_NEEDED:
        return None

    def class_rank(cand_id: int) -> int:
        if own_l2 and l2_map.get(cand_id, set()) & own_l2:
            return 2
        if own_l1 and l1_map.get(cand_id, set()) & own_l1:
            return 1
        return 0

    tiers: dict[int, list[int]] = defaultdict(list)
    for i in other_ids:
        tiers[class_rank(i)].append(i)
    for tier in tiers.values():
        rng.shuffle(tier)
    ordered = tiers[2] + tiers[1] + tiers[0]

    distractors: list[str] = []
    same_l1 = 0
    same_l2 = 0
    for cand_id in ordered:
        if len(distractors) >= DISTRACTORS_NEEDED:
            break
        cand_text = rng.choice(pool[cand_id])
        if cand_text == correct_text or cand_text in distractors:
            continue
        distractors.append(cand_text)
        rank = class_rank(cand_id)
        if rank >= 1:
            same_l1 += 1
        if rank == 2:
            same_l2 += 1
    if len(distractors) < DISTRACTORS_NEEDED:
        return None
    return distractors, same_l1, same_l2


def generate_bank(limit: int | None = None, seed: int = 42) -> list:
    """Returns a list of unsaved BankQuestion instances."""
    from .models import BankQuestion  # avoid a module-level app-registry dependency at import time

    rng = random.Random(seed)
    pools = _collect_pools()
    l1_map, l2_map = _atc_maps()
    names = dict(Ingredient.objects.values_list("id", "name"))

    ingredient_ids = sorted(set().union(*(p.keys() for p in pools.values())))
    if limit:
        ingredient_ids = ingredient_ids[:limit]

    questions = []
    for ing_id in ingredient_ids:
        drug_name = names.get(ing_id)
        if not drug_name:
            continue
        own_l1 = l1_map.get(ing_id, set())
        own_l2 = l2_map.get(ing_id, set())

        for field in QUESTION_FIELDS:
            pool = pools[field]
            own_facts = pool.get(ing_id)
            if not own_facts:
                continue

            cap = FIELD_CAP[field]
            chosen = own_facts if len(own_facts) <= cap else rng.sample(own_facts, cap)

            for correct_text in chosen:
                result = _pick_distractors(rng, pool, ing_id, own_l1, own_l2, l1_map, l2_map, correct_text)
                if result is None:
                    continue
                distractors, same_l1, same_l2 = result
                if same_l1 < 1:
                    continue
                difficulty = "hard" if same_l2 == DISTRACTORS_NEEDED else "medium"

                options = [correct_text, *distractors]
                order = list(range(4))
                rng.shuffle(order)
                shuffled_options = [options[i] for i in order]
                correct_index = order.index(0)

                questions.append(BankQuestion(
                    ingredient_id=ing_id,
                    field=field,
                    prompt_fa=PROMPT_TEMPLATE[field].format(drug=drug_name),
                    options_fa=shuffled_options,
                    correct_index=correct_index,
                    difficulty=difficulty,
                ))
    return questions
