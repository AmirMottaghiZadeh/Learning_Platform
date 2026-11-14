"""Question-focused original paragraphs, without an additional model request."""
import re
from dataclasses import replace

from django.conf import settings

from apps.ai_lab import lexical
from .chunking import token_count


FOCUS_VERSION = 1
BACKGROUND = re.compile(r"\b(?:epidemiology|etiology|aetiology|pathogenesis|pathophysiology|historical background|definition|diagnosis|diagnostic evaluation)\b", re.I)
NON_DRUG = re.compile(r"\b(?:nonpharmacologic\w*|non[ -]drug|behavioral (?:therapy|treatment|interventions)|psychotherapy|surgical treatment)\b", re.I)
LATER_LINE = re.compile(r"\b(?:(?:second|third|fourth)[ -]line|subsequent (?:therapy|treatment)|refractory|treatment[ -]resistant)\b", re.I)
RECOMMENDATION = re.compile(r"\bwe (?:recommend|suggest|prefer|use)\b|\b(?:first[ -]line|initial|preferred) (?:treatment|therapy|medication)|\btreatment of choice\b", re.I)
DOSE_NUMBER = re.compile(r"\d\s*(?:mg|mcg|µg|μg|micrograms?|milligrams?|grams?|mL|units?)\b", re.I)
DURATION = re.compile(r"\bduration\b|\bcontinue (?:therapy|treatment)\b|\bfor (?:\d+|one|two|three|four|six|eight|twelve) (?:days?|weeks?|months?)\b", re.I)
RESTRICTION = re.compile(r"\b(?:avoid|contraindicat\w*|restrict\w*|caution|must not|should not|do not|not recommended|unless|except)\b", re.I)
QUALIFIER = re.compile(RESTRICTION.pattern + r"|\b(?:monitor\w*|maximum|titrate|titration)\b", re.I)
DEPENDENT = re.compile(r"^\s*(?:[-•]\s*)?(?:however\b|unless\b|except\b|only\b|note\b|caution\b|do not\b|avoid\b|this (?:dose|regimen|recommendation|treatment|approach|drug|medication)\b|these (?:doses|patients|recommendations|restrictions)\b|the (?:above|following)\b)", re.I)


def section_key(passage):
    return passage.article_id, passage.target.get("params", {}).get("sectionId"), tuple(passage.heading_path) or (passage.section,)


def _identity(passage):
    return (section_key(passage), passage.content_hash,
            tuple((label.get("quote"), label.get("source_anchor")) for label in passage.context),
            re.sub(r"\s+", " ", passage.text).strip())


def retain_with_context(passages, identifiers):
    """Keep adjacent source qualifications together with their cited evidence.

    Only source ordinals and original short labels may bridge paragraphs;
    neither retrieval rank nor paragraph-ID proximity proves adjacency.
    """
    selected = set(identifiers)
    groups = {}
    for passage in passages:
        if passage.ordinal is not None:
            groups.setdefault(section_key(passage), []).append(passage)
    for group in groups.values():
        group.sort(key=lambda passage: passage.ordinal)
        changed = True
        while changed:
            changed = False
            for left, right in zip(group, group[1:]):
                if left.id not in selected and right.id not in selected:
                    continue
                labels = {label.get("ordinal") for passage in (left, right) for label in passage.context}
                gap = right.ordinal - left.ordinal
                if not 1 <= gap <= 5 or any(ordinal not in labels for ordinal in range(left.ordinal + 1, right.ordinal)):
                    continue
                for candidate in (left, right):
                    if candidate.id not in selected and (DEPENDENT.search(candidate.text) or QUALIFIER.search(candidate.text)):
                        selected.add(candidate.id)
                        changed = True
    return [passage for passage in passages if passage.id in selected]


def focus_passages(passages, question, query, *, lookup_kind="topic", audience="general", intent="general", keywords=()):
    """Rank relevance, retain required roles and prune whole original paragraphs.

    The passage target is soft: required treatment details and attached source
    qualifications may exceed it.
    No sentence, dose, negation, source label or anchor is rewritten.
    """
    before_tokens = sum(token_count(passage.text) for passage in passages)
    if not settings.AI_LAB_HYBRID_EVIDENCE_FOCUS:
        return passages, {"version": FOCUS_VERSION, "enabled": False, "input_passages": len(passages),
                          "selected_passages": len(passages), "input_text_tokens": before_tokens,
                          "selected_text_tokens": before_tokens, "duplicate_passages": 0, "off_scope_passages": 0}
    context = lexical.search_context(question + " " + query, [query], lookup_kind=lookup_kind,
                                     audience=audience, intent=intent, keywords=keywords)
    if "adverse_effects" in context.intents and re.search(r"\b(?:important|major|serious|significant)\b", query, re.I):
        context = replace(context, aspects=tuple(dict.fromkeys([*context.aspects, "important"])))
    therapy_intents = {"treatment", "drug_therapy", "dose", "renal_dose"}
    therapy = (intent in therapy_intents or context.first_line_regimen
               or (intent == "general" and bool(therapy_intents & set(context.intents))))
    specific = set(context.intents) - {"general"}
    maximum = max(1, min(48, settings.AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES))
    target = min(maximum, 12 if therapy or len(specific) > 1 else 8 if not specific else 6)
    rows, seen, duplicates, off_scope = [], set(), 0, 0
    for position, passage in enumerate(passages):
        identity = _identity(passage)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        path = " > ".join(passage.heading_path) or passage.section
        path = path.lower()
        wanted_heading = any(re.search(lexical.INTENTS[name][1], path, re.I) for name in specific)
        roles = set()
        if therapy:
            if RECOMMENDATION.search(passage.text):
                roles.add("recommendation")
            if DOSE_NUMBER.search(passage.text) or (re.search(lexical.REGIMEN_HEADING,path,re.I)
                    and re.search(lexical.REGIMEN_NUMBER,passage.text,re.I)):
                roles.add("regimen")
            if RESTRICTION.search(passage.text):
                roles.add("restriction")
            if re.search(r"\bmonitor\w*\b", passage.text, re.I):
                roles.add("monitoring")
            if DURATION.search(passage.text):
                roles.add("duration")
            if re.search(r"\b(?:target|goal)\b.*\d", passage.text, re.I):
                roles.add("treatment_goal")
        # Only exclude clearly unrelated headings for a specific request.
        # Semantic/tag-only matches with an unfamiliar heading remain eligible.
        unwanted_background = (specific and not ({"diagnosis", "mechanism"} & specific)
                                and BACKGROUND.search(path) and not wanted_heading
                                and not (roles & {"recommendation", "restriction"}))
        unwanted_alternative = ("drug_therapy" in specific and "comparison" not in specific
                                and NON_DRUG.search(path) and not (roles & {"regimen", "restriction"}))
        unwanted_later_line = context.first_line_regimen and context.broad_treatment and LATER_LINE.search(path)
        if unwanted_background or unwanted_alternative or unwanted_later_line:
            off_scope += 1
            continue
        score = (lexical.heading_score(passage.section, passage.heading_path, context)
                 + 2 * lexical.text_score(passage.text, context) + 4 * len(roles)
                 + 4 * lexical.text_score(" ".join(label["quote"] for label in passage.context[-2:]), context))
        rows.append((passage, score, roles, position))
    rows.sort(key=lambda row: (-row[1], row[3]))
    selected = set()
    if rows:
        threshold = rows[0][1] * .35
        eligible = [row for row in rows if row[1] >= threshold]
        # Cover the requested treatment roles before filling the remaining
        # budget with several paragraphs repeating the same point.
        selected.add(eligible[0][0].id)
        # Regimen, duration and contraindications are part of the answer, even
        # when they repeat neither the condition name nor the query wording.
        # Never prune them merely to satisfy an arbitrary paragraph count.
        if therapy:
            selected.update(row[0].id for row in rows if row[2])
        represented = {section_key(row[0]) for row in rows if row[0].id in selected}
        for passage, _, _, _ in eligible:
            key = section_key(passage)
            if len(selected) < target and key not in represented:
                selected.add(passage.id)
                represented.add(key)
        for passage, _, _, _ in eligible:
            if len(selected) >= target:
                break
            selected.add(passage.id)
    focused = retain_with_context([row[0] for row in sorted(rows, key=lambda row: row[3])], selected)
    after_tokens = sum(token_count(passage.text) for passage in focused)
    return focused, {"version": FOCUS_VERSION, "enabled": True, "input_passages": len(passages),
                     "selected_passages": len(focused), "target_passages": target,
                     "input_text_tokens": before_tokens, "selected_text_tokens": after_tokens,
                     "duplicate_passages": duplicates, "off_scope_passages": off_scope}
