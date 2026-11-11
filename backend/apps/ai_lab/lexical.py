"""Bounded, lexical retrieval for AI search only. No embeddings or clinical answers."""
from dataclasses import dataclass
from functools import reduce
import operator
import re

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection
from django.db.models import F, Window
from django.db.models.functions import RowNumber

LEXICAL_VERSION = 3
MAX_TERMS = 24
MAX_LEXICAL_HITS = 96
MAX_RANKED_SECTIONS = 16
MAX_RANKED_PASSAGES = 18
MAX_PASSAGE_CHARACTERS = 24000
MAX_REGIMEN_HITS = 24
REGIMEN_HEADING = r"dos(?:e|es|ing|age)|administration|regimen|application|frequency|duration"
REGIMEN_NUMBER = r"\d\s*(?:mg|mcg|µg|μg|micrograms?|milligrams?|grams?|mL|units?|%)"
REGIMEN_SCHEDULE = r"\b(?:once|twice|three times|four times) (?:a |per )?(?:daily|day|week)|\bevery \d+ hours?\b|\b(?:oral|topical|intravenous|intramuscular)\b"
STOP_WORDS = frozenset("a an and are as at be by for from in is it of on or the to with what which how information drug patient adult children treatment management".split())

# Retrieval hints only: they never constitute an answer or a medical assertion.
INTENTS = {
    "adverse_effects": (r"عارض|عوارض|adverse|side.effect", r"significant adverse|adverse reactions?|side effects?|boxed warnings?|warnings|precautions"),
    "renal_dose": (r"کلیوی|کلیه|renal|kidney", r"renal|kidney|hemodialysis|haemodialysis"),
    "pregnancy": (r"بارداری|باردار|شیرده|pregnan|lactation|breastfeed", r"pregnan|lactation|breastfeed|reproductive"),
    "contraindications": (r"منع مصرف|contraindicat", r"contraindicat|warnings|precautions"),
    "mechanism": (r"مکانیسم|سازوکار|mechanism", r"mechanism|pharmacology|pharmacodynamics"),
    "indications": (r"موارد مصرف|اندیکاسیون|indications?", r"use:|uses|indications?|approved"),
    "monitoring": (r"پایش|پیگیری|monitor|follow.up", r"monitor|follow.up|assess.*response"),
    "dose": (r"دوز|مقدار مصرف|dosing|dosage|\bdose\b", r"dosing|dosage|administration|\bdose\b"),
    "comparison": (r"تفاوت|مقایسه|comparison|compare|versus", r"comparison|comparative|versus|selection|choosing"),
    "prevention": (r"پیشگیری|prevent", r"prevent|prophylaxis"),
    "drug_therapy": (r"دارودرمانی|دارو درمانی|درمان دارویی|drug therapy|pharmacotherap", r"pharmacologic|pharmacotherap|drug therapy|medication|drug treatment"),
    "treatment": (r"درمان|treat|management|therapy", r"treatment|management|therapy|therapies|recommendations|suggested approach"),
    "diagnosis": (r"تشخیص|diagnos|evaluation", r"diagnos|evaluation|clinical manifestations|differential"),
    "general": (r"(?!)", r"summary|overview"),
}
HINTS = {
    "adverse_effects": "adverse reactions side effects warnings precautions",
    "renal_dose": "renal impairment kidney dialysis dosing",
    "pregnancy": "pregnancy breastfeeding lactation",
    "contraindications": "contraindications warnings precautions",
    "mechanism": "mechanism pharmacology",
    "indications": "indications approved uses",
    "monitoring": "monitoring follow up response",
    "dose": "dosing dosage administration",
    "comparison": "comparison versus selection",
    "prevention": "prevention prophylaxis",
    "drug_therapy": "pharmacologic pharmacotherapy medication drug therapy",
    "treatment": "treatment therapy management recommendations",
    "diagnosis": "diagnosis evaluation differential",
    "general": "",
}


def tokens(text):
    return re.findall(r"[a-z][a-z0-9]{1,39}", text.lower())


@dataclass(frozen=True)
class SearchContext:
    intents: tuple
    terms: tuple
    concepts: tuple
    aspects: tuple = ()
    lookup_kind: str = "topic"
    audience: str = "general"
    broad_treatment: bool = False
    first_line_regimen: bool = False


def first_line_treatment(question):
    text = re.sub(r"[\u200c\u200d\u0640]", " ", question).replace("ي", "ی").replace("ك", "ک")
    return bool(re.search(r"خط\s*(?:اول|۱|1)\s*درمان|(?:درمان|دارو(?:ی|های)?)\s*(?:انتخابی\s*)?(?:خط\s*)?(?:اول|اولیه)\b"
                          r"|\bfirst[ -]+line\s+(?:treatment|therapy|drug|medication|management|regimen)\b", text, re.I))


def regimen_score(text, heading=""):
    # Retrieval cues only, never a claim that this dose belongs to a recommended drug.
    return (4 if re.search(REGIMEN_NUMBER, text, re.I) else 0) + (2 if re.search(REGIMEN_SCHEDULE, text, re.I) else 0) + (1 if re.search(REGIMEN_HEADING, heading, re.I) else 0)


def search_context(question, queries=(), *, lookup_kind="topic", audience="general", intent="general", keywords=()):
    first_line = first_line_treatment(question)
    detected = [name for name, (pattern, _) in INTENTS.items() if re.search(pattern, question, re.I)]
    if first_line and "treatment" not in detected:
        detected.append("treatment")
    if intent in INTENTS and intent != "general" and intent not in detected:
        detected.insert(0, intent)
    detected = detected or ["general"]
    # Preserve explicit question terms before retrieval hints. Bound every input.
    concepts = list(dict.fromkeys(word for phrase in queries[:2] for word in tokens(phrase) if word not in STOP_WORDS))[:12]
    aspects = tuple(dict.fromkeys(word for phrase in keywords[:8] for word in tokens(phrase)
                                 if word not in STOP_WORDS and word not in concepts))[:12]
    words = concepts + [word for phrase in keywords[:8] for word in tokens(phrase)] + tokens(question)
    words += [word for name in detected for word in tokens(HINTS[name])]
    if first_line:
        words += tokens("dose dosing dosage administration regimen frequency duration")
    terms = tuple(dict.fromkeys(word for word in words if word not in STOP_WORDS))[:MAX_TERMS]
    specific_scope = re.search(r"موضعی|سیستمیک|شدید|خفیف|مقاوم|شکست|باردار|کلیوی|کلیه|حساسیت|آلرژی|topical|systemic|severe|mild|refractory|failure|pregnan|renal|allerg", question, re.I)
    broad = lookup_kind == "topic" and bool({"treatment", "drug_therapy"} & set(detected)) and not specific_scope
    return SearchContext(tuple(detected), terms, tuple(concepts), aspects, lookup_kind, audience, broad, first_line)


def heading_score(heading, path, context):
    own, ancestors = heading.lower(), " ".join(path[:-1]).lower()
    score = 0.0
    for intent in context.intents:
        pattern = INTENTS[intent][1]
        if re.search(pattern, own):
            score += 12
        elif re.search(pattern, ancestors):
            score += 6
    score += min(6, len(set(tokens(own)) & set(context.terms)))
    score += min(3, len(set(tokens(ancestors)) & set(context.terms))) * .5
    # A specifically requested aspect (e.g. "test of cure") must outrank the
    # incidental word "treatment" in "after treatment". These are query hints,
    # never terms derived from expected sources or a guessed clinical answer.
    score += min(12, 4 * len(set(tokens(own)) & set(context.aspects)))
    score += min(6, 2 * len(set(tokens(ancestors)) & set(context.aspects)))
    if "adverse_effects" in context.intents and set(context.aspects) & {"important", "major", "serious", "significant"}:
        # Match the explicitly requested importance qualifier. A long general
        # frequency list must not displace the source's significant-reactions
        # section solely because it repeats the drug name more often.
        if "significant" in own and "adverse" in own:
            score += 8
        elif "significant" in ancestors and "adverse" in ancestors:
            score += 4
    if re.search(r"summary|recommendations|suggested approach", own):
        score += 2
    if context.first_line_regimen:
        if re.search(r"first.line|initial (?:treatment|therapy)|summary|recommendations|suggested approach", own):
            score += 8
        if re.search(REGIMEN_HEADING, own):
            score += 10
        elif re.search(REGIMEN_HEADING, ancestors):
            score += 5
    return score


def text_score(text, context):
    words = set(tokens(text))
    # Saturating term coverage, not length or repeated keyword frequency.
    score = (len(words & set(context.terms)) + min(3, len(words & set(context.concepts)))
             + min(8, 2 * len(words & set(context.aspects))))
    if (context.broad_treatment or context.first_line_regimen) and re.search(r"\bwe (?:suggest|recommend)\b|\b(?:initial|first.line) (?:treatment|therapy)\b", text, re.I):
        score += 8
    if context.first_line_regimen:
        score += regimen_score(text)
    return score


def rank_topics(articles, context):
    """Stable reorder of the canonical tagged candidates; never invent/drop IDs."""
    if context is None:
        return articles

    def score(article):
        title = article["title"].lower()
        pediatric = bool(re.search(r"\bpediatric|\bpaediatric|\bchildren|\binfants?\b", title))
        adult = bool(re.search(r"\badults?\b", title))
        patient = bool(re.search(r"\bpatient\b", title))
        drug = "drug information" in title
        # Explicit monograph/audience priorities remain stronger than text overlap.
        priority = 0
        if context.lookup_kind == "drug":
            if context.audience == "patient":
                priority = 5 if patient else 4 if drug and not pediatric else 1
            elif context.audience == "pediatric":
                priority = 5 if drug and pediatric else 4 if drug and not patient else 3 if patient else 1
            else:
                priority = 5 if drug and not patient and not pediatric else 4 if patient else 3 if adult else 1
        elif context.audience == "patient":
            priority = 3 if patient else 0
        elif context.audience == "pediatric":
            priority = 3 if pediatric else -3 if adult else 0
        elif context.audience == "adult":
            priority = -3 if pediatric else 2 if adult else 0
        relevance = heading_score(title, [], context)
        relevance += min(6, len(set(tokens(title)) & set(context.concepts)))
        if context.broad_treatment and re.search(r"overview of management|approach to (?:the )?(?:management|treatment)|initial management|initial treatment", title):
            relevance += 18
        return (-priority, -relevance)
    return sorted(articles, key=score)


def rank_memory_sections(sections, context, audit):
    """Equivalent bounded fallback when the prepared generation is unavailable."""
    ranked = []
    for section in sections:
        passages = sorted(section["passages"], key=lambda p: -text_score(p.text, context))
        strength = heading_score(section["heading"], section.get("heading_path", []), context)
        strength += min(6, max((text_score(p.text, context) for p in passages), default=0))
        ranked.append((strength, {**section, "passages": passages}))
    ranked.sort(key=lambda pair: -pair[0])
    if len(ranked) > MAX_RANKED_SECTIONS:
        audit["limited"] = True
    audit.update(lexical_engine="memory", lexical_version=LEXICAL_VERSION,
                 lexical_candidate_sections=len(ranked))
    return [section for _, section in ranked[:MAX_RANKED_SECTIONS]]


def _query(context):
    return reduce(operator.or_, (SearchQuery(term, config="english", search_type="plain") for term in context.terms)) if context.terms else None


def prepared_sections(article, context, section_offset, passage_offset, audit):
    """Search within one authorized, fresh article, including sections after #60."""
    from .retrieval import Passage

    groups = list(article.sections.filter(retrieval_order__isnull=False).order_by("retrieval_order"))
    blocks = article.paragraphs.filter(retrieval_number__isnull=False)
    query = _query(context)
    if connection.vendor != "postgresql":
        # Development/test backends have no PostgreSQL FTS operators.
        hits = list(blocks.order_by("ordinal").values())
        for block in hits:
            block["rank"] = text_score(block["text"], context) / 10
        hits.sort(key=lambda row: (-row["rank"], row["ordinal"]))
        hits = hits[:MAX_LEXICAL_HITS]
    elif query is not None:
        vector = SearchVector("text", config="english")
        hits = list(blocks.annotate(vector=vector).filter(vector=query)
                    .annotate(rank=SearchRank(vector, query, normalization=32))
                    .order_by("-rank", "ordinal").values("id", "section_id", "retrieval_number", "ordinal",
                                                         "text", "source_anchor", "rank")[:MAX_LEXICAL_HITS])
    else:
        hits = []
    strengths = {}
    for block in hits:
        strengths[block["section_id"]] = max(strengths.get(block["section_id"], 0), min(6, block["rank"] * 60))
    groups.sort(key=lambda group: -(heading_score(group.heading, group.heading_path, context) + strengths.get(group.pk, 0)))
    selected = groups[:MAX_RANKED_SECTIONS]
    selected_ids = {group.pk for group in selected}
    if context.first_line_regimen and connection.vendor == "postgresql":
        # A regimen may name only the drug and numbers, without the disease or
        # "dosing". Bound this supplementary read to sections of this one article.
        details = list(blocks.filter(section_id__in=selected_ids, text__iregex=REGIMEN_NUMBER).order_by("ordinal")
                       .values("id", "section_id", "retrieval_number", "ordinal", "text", "source_anchor")[:MAX_REGIMEN_HITS])
        detail_ids = {row["id"] for row in details}
        hits = [row for row in hits if row["id"] not in detail_ids][:MAX_LEXICAL_HITS - len(details)]
        hits += [{**row, "rank": 0} for row in details]
        audit["regimen_candidate_hits"] = len(details)
    # Preserve opening context/qualifications even when no query word occurs there.
    opening = list(blocks.filter(section_id__in=selected_ids).annotate(
        position=Window(expression=RowNumber(), partition_by=[F("section_id")], order_by=F("ordinal").asc())
    ).filter(position__lte=2).order_by("ordinal").values("id", "section_id", "retrieval_number", "ordinal", "text", "source_anchor"))
    pooled = {row["id"]: {**row, "rank": 0} for row in opening}
    pooled.update({row["id"]: row for row in hits if row["section_id"] in selected_ids})
    grouped = {group.pk: [] for group in selected}
    for row in pooled.values():
        grouped[row["section_id"]].append(row)
    result = []
    for group in selected:
        rows = sorted(grouped[group.pk], key=lambda row: (-(row["rank"] + text_score(row["text"], context) * .02), row["ordinal"]))
        passages = [Passage(id=f"P{passage_offset + row['retrieval_number']}", article_id=article.source_id,
            title=article.title, section=group.heading, text=row["text"], content_hash=article.content_hash,
            target={"screen": "uptodateArticle", "params": {"id": article.source_id, "title": article.title,
                "sectionId": group.source_id, "searchAnchor": row["source_anchor"], "searchContentHash": article.content_hash}})
            for row in rows]
        if passages:
            result.append({"id": f"T{section_offset + group.retrieval_order + 1}", "article_id": article.source_id,
                "title": article.title, "heading": group.heading, "preview": " ".join(p.text for p in passages[:2])[:280],
                "passages": passages})
    audit.update(lexical_engine="postgresql_fts" if connection.vendor == "postgresql" else "memory",
                 lexical_version=LEXICAL_VERSION, lexical_candidate_sections=len(groups), lexical_hits=len(hits))
    if len(groups) > len(selected) or article.eligible_block_count > len(pooled):
        audit["limited"] = True
    return result, article.eligible_block_count


def bounded_passages(sections, selected_ids, audit):
    by_id = {section["id"]: section for section in sections}
    groups = [by_id[identifier]["passages"] for identifier in selected_ids]
    candidates = [group[depth] for depth in range(max(map(len, groups), default=0)) for group in groups if depth < len(group)]
    result, characters = [], 0
    for passage in candidates:
        if len(result) >= MAX_RANKED_PASSAGES:
            break
        if characters + len(passage.text) > MAX_PASSAGE_CHARACTERS:
            continue
        result.append(passage)
        characters += len(passage.text)
    if len(result) < len(candidates):
        audit["limited"] = True
    audit.update(selected_sections=len(groups), selected_passages=len(result), selected_passage_characters=characters)
    return result
