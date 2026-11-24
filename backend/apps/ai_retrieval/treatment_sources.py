"""Confirm treatment scope against indexed headings and the start of their text."""
from collections import defaultdict
import re

from django.db.models import F, Window
from django.db.models.functions import RowNumber

from apps.ai_lab import lexical
from apps.ai_lab.models import ReferenceParagraph, ReferenceSection
from apps.ai_lab.section_tree import MANAGEMENT_HEADING, THERAPY_HEADING
from .chunking import source_metadata
from .evidence import RECOMMENDATION


PROBE_ARTICLES = 24
PROBE_SECTIONS = 8
OPENING_PARAGRAPHS = 4


def general_recommendation(text, *, inherited_later=False):
    later = inherited_later
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        match = lexical.LATER_TREATMENT_TOPIC.search(sentence)
        opening = sentence[:match.start()] if match else sentence
        if lexical.initial_match((), opening) > 0 and RECOMMENDATION.search(opening):
            return True
        later = later or match is not None
        if not later and RECOMMENDATION.search(sentence):
            return True
    return False


def treatment_coverage(generation, article_ids, scope, audience):
    """Return positive proof of general care or a negative later-line-only signal."""
    if not scope or scope.stage not in {"general", "initial"} or not article_ids:
        return {}
    titles = list(dict.fromkeys(article_ids))[:PROBE_ARTICLES]
    sections = defaultdict(list)
    rows = ReferenceSection.objects.filter(
        article__generation_id=generation, article__source_id__in=titles, retrieval_order__isnull=False,
    ).values_list("pk", "article__source_id", "article__title", "heading", "heading_path").order_by("article_id", "ordinal")
    coverage = {}
    for pk, identifier, title, heading, path in rows:
        path = path or [heading]
        body = " > ".join(path)
        if not (THERAPY_HEADING.search(body) or MANAGEMENT_HEADING.search(body) or lexical.after_initial_therapy(path)):
            continue
        population, _ = source_metadata(title, path)
        if {audience, population} == {"adult", "pediatric"}:
            continue
        if lexical.after_initial_therapy(path):
            coverage.setdefault(identifier, -1)
            continue
        own_heading = bool(THERAPY_HEADING.search(heading) or MANAGEMENT_HEADING.search(heading))
        priority = (-lexical.initial_match(path), not own_heading)
        sections[identifier].append((priority, pk))
    inspected = {
        pk: identifier for identifier, values in sections.items()
        for _, pk in sorted(values, key=lambda item: item[0])[:PROBE_SECTIONS]
    }
    openings = ReferenceParagraph.objects.filter(section_id__in=inspected, retrieval_number__isnull=False).annotate(
        section_rank=Window(RowNumber(), partition_by=[F("section_id")], order_by=F("ordinal").asc()),
    ).filter(section_rank__lte=OPENING_PARAGRAPHS).order_by("section_id", "ordinal").values_list("section_id", "text")
    general, restricted, later_sections = set(), set(), set()
    for section_id, text in openings:
        identifier = inspected[section_id]
        if general_recommendation(text, inherited_later=section_id in later_sections):
            coverage[identifier] = 2
            later_sections.discard(section_id)
        elif section_id in later_sections or lexical.LATER_TREATMENT_TOPIC.search(text):
            later_sections.add(section_id)
            restricted.add(identifier)
        else:
            general.add(identifier)
    for identifier in restricted - general:
        coverage.setdefault(identifier, -1)
    for identifier in general:
        coverage[identifier] = max(coverage.get(identifier, 0), 1)
    return coverage
