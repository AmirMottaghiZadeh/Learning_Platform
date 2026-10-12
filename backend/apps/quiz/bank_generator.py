"""Rule-based (no LLM) MCQ generation from the drug flashcard facts.

The bank asks only about what the flashcards teach: the five card sections
(apps.flashcards.sections) -- indication, common side effects, serious side
effects, dosage forms, and contraindications / boxed warning -- using the
exact Persian facts build_flashcards stored (FlashcardFact), so a learner is
never quizzed on something their cards don't show. Run build_flashcards
first.

Each drug gets QUESTIONS_PER_SECTION questions per section (2 x 5 = 10): its
own facts are the candidate correct answers; three distractors come from
other drugs' facts in the same section, biased *toward* the subject's own
ATC class rather than away from it -- a distractor from an unrelated class
can be eliminated by category alone, which is what makes a question easy. A
question is kept only if at least one distractor shares the subject's ATC
anatomical section (L1), and never uses a distractor that is also one of the
subject's own facts. `difficulty` is "hard" when all three share its ATC
subclass (L2), "medium" otherwise.

A drug with fewer than two usable facts in a section, or too few same-class
peers there, simply gets fewer questions for it -- there is no padding and
no invented distractor.
"""

import random
from collections import Counter, defaultdict

from apps.drugs.models import Ingredient
from apps.flashcards.models import FlashcardFact
from apps.flashcards.sections import SECTION_KEYS

QUESTIONS_PER_SECTION = 2

PROMPT_TEMPLATE = {
    "indication": "کدام مورد زیر از موارد مصرف «{drug}» است؟",
    "adr_common": "کدام مورد زیر از عوارض شایع «{drug}» است؟",
    "adr_serious": "کدام مورد زیر از عوارض مهم و جدی «{drug}» است؟",
    "dosage_forms": "کدام مورد زیر از اشکال دارویی «{drug}» است؟",
    "contra_boxed": "کدام مورد زیر از منع مطلق مصرف یا هشدار جعبه‌سیاه «{drug}» است؟",
}

# A fact this common across different drugs in the same section is
# boilerplate, not a distinguishing fact about any one of them.
MAX_GLOBAL_REPEAT = 3
DISTRACTORS_NEEDED = 3


def _collect_pools() -> dict[str, dict[int, list[str]]]:
    """section -> ingredient_id -> [Persian fact, ...] (card order), with
    corpus-wide boilerplate dropped."""
    pools: dict[str, dict[int, list[str]]] = {key: defaultdict(list) for key in SECTION_KEYS}
    counts: dict[str, Counter] = {key: Counter() for key in SECTION_KEYS}
    facts = (
        FlashcardFact.objects.filter(lang="fa")
        .order_by("ingredient_id", "section", "order")
        .values_list("ingredient_id", "section", "text")
    )
    for ing_id, section, text in facts.iterator():
        if text in pools[section][ing_id]:
            continue
        pools[section][ing_id].append(text)
        counts[section][text] += 1

    for key in SECTION_KEYS:
        for ing_id, texts in list(pools[key].items()):
            kept = [t for t in texts if counts[key][t] < MAX_GLOBAL_REPEAT]
            if kept:
                pools[key][ing_id] = kept
            else:
                del pools[key][ing_id]
    return pools


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
    own_facts: set[str],
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
        if cand_text in own_facts or cand_text in distractors:
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

        for section in SECTION_KEYS:
            pool = pools[section]
            own_facts = pool.get(ing_id)
            if not own_facts or len(own_facts) < QUESTIONS_PER_SECTION:
                continue
            own_set = set(own_facts)
            candidates = list(own_facts)
            rng.shuffle(candidates)

            made = 0
            for correct_text in candidates:
                if made >= QUESTIONS_PER_SECTION:
                    break
                result = _pick_distractors(rng, pool, ing_id, own_l1, own_l2, l1_map, l2_map, own_set)
                if result is None:
                    continue
                distractors, same_l1, same_l2 = result
                if same_l1 < 1:
                    continue
                difficulty = "hard" if same_l2 == DISTRACTORS_NEEDED else "medium"

                options = [correct_text, *distractors]
                order = list(range(4))
                rng.shuffle(order)
                questions.append(BankQuestion(
                    ingredient_id=ing_id,
                    field=section,
                    prompt_fa=PROMPT_TEMPLATE[section].format(drug=drug_name),
                    options_fa=[options[i] for i in order],
                    correct_index=order.index(0),
                    difficulty=difficulty,
                ))
                made += 1
    return questions
