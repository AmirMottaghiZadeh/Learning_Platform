"""Question generation for the quiz.

This first pass builds ATC drug-class identification questions (drug -> class and
class -> drug), which only needs the ATC data every ingredient already has. A
richer generator (contraindications, interactions, dosing) is a later pass.
"""

import random

from apps.drugs.models import AtcCategory, Ingredient

# category -> ATC L1 letter(s) to draw from ("" = any)
CATEGORY_L1 = {
    "general": "",
    "antibiotics": "J",
    "cardio": "C",
    "interactions": "",  # narrowed to drugs that have interaction content, below
}


def _pool(category):
    """[(ingredient, l2_code), ...] for the category."""
    qs = Ingredient.objects.filter(atc_codes__isnull=False).prefetch_related(
        "atc_codes", "sections"
    ).distinct()
    l1 = CATEGORY_L1.get(category, "")
    rows = []
    for ingredient in qs:
        l2_codes = sorted({c.code[:3] for c in ingredient.atc_codes.all()})
        if not l2_codes:
            continue
        if l1 and not any(code[0] == l1 for code in l2_codes):
            continue
        if category == "interactions":
            has_int = any(
                s.field == "drug_interactions" and (s.summary_fa or s.summary_en)
                for s in ingredient.sections.all()
            )
            if not has_int:
                continue
        rows.append((ingredient, l2_codes[0]))
    return rows


def generate_questions(category, count):
    pool = _pool(category)
    if len(pool) < 4:  # not enough for distractors -> fall back to general
        pool = _pool("general")
    names = {
        c.code: (c.name_fa, c.name_en)
        for c in AtcCategory.objects.filter(level=2)
    }
    rng = random.Random()
    rng.shuffle(pool)

    questions = []
    used_subjects = set()
    for ingredient, l2 in pool:
        if len(questions) >= count:
            break
        if l2 not in names or ingredient.slug in used_subjects:
            continue
        correct_fa, correct_en = names[l2]
        other_codes = [c for c in names if c != l2]
        if len(other_codes) < 3:
            break
        used_subjects.add(ingredient.slug)

        if rng.random() < 0.5:
            # drug -> class
            distractors = rng.sample(other_codes, 3)
            opts = [(correct_fa, correct_en)] + [names[c] for c in distractors]
            rng.shuffle(opts)
            questions.append({
                "prompt_fa": f"«{ingredient.name}» در کدام دستهٔ دارویی قرار می‌گیرد؟",
                "prompt_en": f"Which drug class does {ingredient.name} belong to?",
                "options_fa": [o[0] for o in opts],
                "options_en": [o[1] for o in opts],
                "correct_index": next(i for i, o in enumerate(opts) if o[0] == correct_fa),
                "subject_slug": ingredient.slug,
            })
        else:
            # class -> drug
            same_class = [
                i for i, code in pool
                if code == l2 and i.slug != ingredient.slug
            ]
            others = [i for i, code in pool if code != l2]
            if not others or len(others) < 3:
                continue
            correct_drug = ingredient
            distractor_drugs = rng.sample(others, 3)
            opts = [correct_drug] + distractor_drugs
            rng.shuffle(opts)
            questions.append({
                "prompt_fa": f"کدام دارو در دستهٔ «{correct_fa}» است؟",
                "prompt_en": f"Which drug belongs to “{correct_en}”?",
                "options_fa": [d.name for d in opts],
                "options_en": [d.name for d in opts],
                "correct_index": opts.index(correct_drug),
                "subject_slug": ingredient.slug,
            })
    return questions
