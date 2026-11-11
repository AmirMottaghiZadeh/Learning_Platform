"""Deterministic evidence selection after lexical retrieval, without model calls."""
from django.conf import settings

from . import lexical

SELECTION_VERSION = 2
BATCH_SIZE = 6
LEADING_PASSAGES = 3


def enabled():
    # Disabling lexical retrieval retains the phase-two rollback contract.
    return settings.AI_LAB_LOCAL_SELECTION_ENABLED and settings.AI_LAB_LEXICAL_ENABLED


def select_evidence(sections, audit, *, context=None):
    """Favor the strongest section, then cover alternatives within a fixed budget.

    Sections and their paragraphs have already been ranked for this question.
    Put three paragraphs from the strongest section into the first batch, then
    cover the next sections. This leaves room for qualifications, and avoids
    sending the opening paragraphs of a long monograph in source order.
    Later batches cover lower-ranked sections before deepening the leaders.
    Selection is retrieval, never a claim that the evidence answers the question.
    """
    groups = [section for section in sections[:lexical.MAX_RANKED_SECTIONS] if section["passages"]]
    schedule = []
    if groups:
        schedule.extend((groups[0], p) for p in groups[0]["passages"][:LEADING_PASSAGES])
        if context is not None and context.first_line_regimen:
            details = [(group, passage) for group in groups for passage in group["passages"]
                       if lexical.regimen_score(passage.text, group.get("heading", ""))]
            details.sort(key=lambda pair: -lexical.regimen_score(pair[1].text, pair[0].get("heading", "")))
            # Two source regimens can accompany the recommendation in batch one;
            # no medication name or dose is supplied by retrieval itself.
            leading_ids = {passage.id for _, passage in schedule}
            schedule.extend([pair for pair in details if pair[1].id not in leading_ids][:2])
        schedule.extend((group, group["passages"][0]) for group in groups[1:])
        # Cover every candidate section before returning to a long leader.
        for depth in range(1, max(len(group["passages"]) for group in groups)):
            for number, group in enumerate(groups):
                if depth < len(group["passages"]) and not (number == 0 and depth < LEADING_PASSAGES):
                    schedule.append((group, group["passages"][depth]))

    passages, section_ids, seen, characters = [], [], set(), 0
    for section, passage in schedule:
        if len(passages) >= lexical.MAX_RANKED_PASSAGES:
            break
        if passage.id in seen or characters + len(passage.text) > lexical.MAX_PASSAGE_CHARACTERS:
            continue
        # Retain whole original paragraphs, IDs, content hashes and targets.
        seen.add(passage.id)
        passages.append(passage)
        characters += len(passage.text)
        if section["id"] not in section_ids:
            section_ids.append(section["id"])
    audit.update(selection_engine="local", selection_version=SELECTION_VERSION,
                 selected_section_ids=section_ids, selected_sections=len(section_ids),
                 selected_passages=len(passages), selected_passage_characters=characters)
    if len(passages) < len(schedule) or len(sections) > len(groups):
        audit["limited"] = True
    return section_ids, passages
