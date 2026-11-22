"""Expand stored outline relationships and read each branch fairly."""
from collections import defaultdict
import re

from django.db.models import F, Window
from django.db.models.functions import RowNumber

THERAPY_HEADING = re.compile(
    r"\b(?:drug therapy|pharmacotherap\w*|pharmacologic\w* (?:therapy|treatment|management)|"
    r"medications?|drug selection|dos(?:e|ing|age)|regimens?)\b", re.I,
)
MANAGEMENT_HEADING = re.compile(r"\b(?:treatment|management)\b", re.I)


def therapy_root(section, by_id):
    management = None
    while section:
        if THERAPY_HEADING.search(section.heading):
            return section
        if management is None and MANAGEMENT_HEADING.search(section.heading):
            management = section
        section = by_id.get(section.parent_id)
    return management


def expand_sections(sections, roots):
    children = defaultdict(list)
    for section in sections:
        children[section.parent_id].append(section.pk)
    selected = set(roots)
    pending = list(selected)
    while pending:
        for child in children[pending.pop()]:
            if child not in selected:
                selected.add(child)
                pending.append(child)
    return selected


def balanced_paragraphs(rows, limit):
    """Take a paragraph from each heading before the second from any heading."""
    return rows.annotate(branch_rank=Window(
        expression=RowNumber(), partition_by=[F("section_id")], order_by=F("ordinal").asc(),
    )).order_by("branch_rank", "article_id", "section__ordinal", "ordinal", "pk")[:limit]
