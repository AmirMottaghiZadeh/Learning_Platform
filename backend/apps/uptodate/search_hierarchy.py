"""Article-first retrieval; independent of Django and of any model runtime.

Article selection reads titles only. Section selection reads the selected
article's outline. Passage backends receive an explicit, versioned scope and
must never broaden it. This module is not wired to the public search API.

The title catalog and the small word lists below are the pre-concept
baseline; phase 2 of docs/search/README.md replaces them with UpToDate's
concept dictionary and a reviewed Persian lexicon.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import math
import re
import unicodedata
from typing import Callable

from .search_extraction import ExtractedArticle


HIERARCHY_VERSION = "utd-hierarchy-v3"
_WORDS = re.compile(r"[^\W_]+", re.UNICODE)
_TAGS = re.compile(r"<[^>]*>")
_DRUG_TITLE = re.compile(r"^(.+?):\s*(?:(Pediatric|Patient)\s+)?drug information$", re.I)
_STOP = frozenset("a an and or of in on for the to with is what how information drug during associated due در از و یا به برای چیست چه چگونه زمان".split())
# A small, explicit pilot vocabulary. No inferred transliteration or clinical
# answer generation. Uncovered Persian terms remain visible in the query.
_TERM_GROUPS = {
    "dose": "dose doses dosing dosage دوز دوزهای دوزی",
    "adjust": "adjust adjusting adjustment adjustments تنظیم تعدیل",
    "kidney": "kidney kidneys renal کلیه کلیوی",
    "liver": "liver hepatic کبد کبدی",
    "impairment": "impairment impaired insufficiency نارسایی اختلال",
    "disease": "disease diseases بیماری",
    "pediatric": "pediatric paediatric pediatrics children child infant neonatal کودک کودکان اطفال نوزاد نوزادان",
    "adult": "adult adults بزرگسال بزرگسالان",
    "patient": "patient patients consumer بیمار بیماران",
    "interaction": "interaction interactions تداخل تداخلات",
    "bleeding": "bleeding hemorrhage خونریزی",
    "hiv": "hiv antiretroviral ایدز",
    "compare": "compare comparison versus vs مقایسه",
    "management": "management manage treatment treat treating therapy therapies therapeutic درمان مدیریت",
    "diagnosis": "diagnosis diagnostic diagnose evaluation evaluate assessment screening ارزیابی تشخیص",
    "prevention": "prevention prevent prophylaxis prophylactic thromboprophylaxis پیشگیری",
    "illness": "illness sick intercurrent",
    "allergy": "allergy allergic allergies hypersensitivity حساسیت",
    "antibiotic": "antibiotic antibiotics antimicrobial antimicrobials",
    "antidepressant": "antidepressant antidepressants",
    "pregnancy": "pregnancy pregnant antenatal prenatal بارداری باردار",
    "thrombosis": "thrombosis thromboembolism thromboembolic thrombotic dvt vte",
    "opioid": "opioid opioids opiate opiates",
    "overdose": "overdose poisoning intoxication toxicity مسمومیت",
    "anticoagulant": "anticoagulant anticoagulants anticoagulation",
    "formulation": "formulation formulations forms",
    "insulin": "insulin انسولین",
    "angioedema": "angioedema آنژیوادم آنژیوادما",
    "inhibitor": "inhibitor inhibitors مهارکننده مهارکنندگان",
    "nsaid": "nsaid nsaids",
    "injury": "injury injuries آسیب",
    "asthma": "asthma آسم",
    "exacerbation": "exacerbation exacerbations تشدید",
    "stroke": "stroke سکته",
    "ischemic": "ischemic ischaemic ischemia ایسکمیک",
    "hypothyroidism": "hypothyroidism",
    "anemia": "anemia anaemia کمخونی",
    "iron": "iron آهن",
    "deficiency": "deficiency فقر",
    "rheumatoid": "rheumatoid روماتوئید",
    "arthritis": "arthritis آرتریت",
    "hypertension": "hypertension hypertensive antihypertensive ضدفشارخون پرفشاری",
    "falls": "fall falls سقوط",
    "medication": "medication medications دارو داروها داروهای",
    "initial": "initial اولیه",
    "acute": "acute حاد",
    "chronic": "chronic مزمن",
    "severe": "severe شدید",
    "elderly": "elderly older geriatric سالمند سالمندان",
    "iv": "iv intravenous وریدی",
    "im": "im intramuscular عضلانی",
    "sc": "sc subcutaneous زیرجلدی",
    "oral": "oral خوراکی",
    "bolus": "bolus بولوس",
    "infusion": "infusion انفوزیون",
    "product": "product products محصول فرآورده فراورده",
    "administration": "administration تجویز",
    "mg": "mg milligram milligrams میلیگرم",
    "mcg": "mcg microgram micrograms میکروگرم",
}
_TERM_MAP = {term: canonical for canonical, terms in _TERM_GROUPS.items() for term in terms.split()}
_FACETS = frozenset({"dose", "kidney", "liver", "interaction", "pregnancy", "bleeding"})
# Generic intent/context words must never become the primary subject. These
# rules are shared across queries, not keyed by evaluation IDs or source IDs.
_GENERIC = _FACETS | frozenset({"adjust", "impairment", "disease", "management", "diagnosis",
    "prevention", "illness", "pediatric", "adult", "patient", "initial", "acute", "chronic",
    "severe", "suspected", "selection", "medications", "medication", "ill", "within", "window",
    "time", "older", "elderly", "induced", "related", "associated", "major", "general",
    "complications", "use", "using", "antibiotic", "formulation", "mg", "milligrams", "ml", "compare",
    "medication", "reduction", "reduce", "deprescribing", "کاهش", "خون", "میلی", "گرم"})
_NAMED_SUBJECTS = frozenset({"angioedema", "insulin", "nsaid", "asthma", "stroke", "hypothyroidism",
    "anemia", "rheumatoid", "arthritis", "hypertension", "falls", "opioid", "thrombosis",
    "penicillin", "antidepressant", "gastrointestinal"})
_RELATED_SUBJECTS = {"insulin": {"diabetes"}, "naloxone": {"opioid"},
                     "apixaban": {"anticoagulant"}, "rivaroxaban": {"anticoagulant"},
                     "warfarin": {"anticoagulant"}, "dabigatran": {"anticoagulant"}}
# Seed aliases are names only; the canonical entity must exist in this snapshot.
# Callers can supply a reviewed, versioned dictionary to replace these seeds.
SEED_ALIASES = {
    "apixaban": ("آپیکسابان", "اپیکسابان"),
    "rivaroxaban": ("ریواروکسابان",),
    "warfarin": ("وارفارین",),
    "dabigatran": ("دابیگاتران",),
    "metformin": ("متفورمین",),
    "vancomycin": ("وانکومایسین",),
    "gabapentin": ("گاباپنتین",),
    "fluconazole": ("فلوکونازول",),
    "aspirin": ("آسپرین", "اسپرین"),
    "naloxone": ("نالوکسان",),
    "acetaminophen": ("استامینوفن", "پاراستامول", "paracetamol"),
    "acetaminophen paracetamol": ("acetaminophen", "paracetamol", "استامینوفن", "پاراستامول"),
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", unescape(_TAGS.sub(" ", text)))
    text = text.translate(str.maketrans({"ي": "ی", "ك": "ک", "\u200c": " "}))
    return " ".join(_WORDS.findall(text.casefold()))


def terms(text: str) -> tuple[str, ...]:
    text = re.sub(r"\bi\.v\.", "iv", text, flags=re.I)
    normalized = " " + normalize(text) + " "
    for phrase, canonical in {
        "داخل وریدی": "iv",
        "زیر جلدی": "sc",
        "میلی گرم": "mg",
        "میکرو گرم": "mcg",
        "nonsteroidal anti inflammatory drugs": "nsaid",
        "nonsteroidal anti inflammatory": "nsaid",
        "ضدالتهاب غیراستروئیدی": "nsaid",
        "کم کاری تیروئید": "hypothyroidism",
        "کم خونی": "anemia",
        "دستگاه گوارش فوقانی": "upper gastrointestinal",
    }.items():
        normalized = normalized.replace(" " + phrase + " ", " " + canonical + " ")
    return tuple(_TERM_MAP.get(word, word) for word in normalized.split() if word not in _STOP)


def lexical_scores(query: tuple[str, ...], documents: list[tuple[str, ...]]) -> list[float]:
    """Small local BM25 reference backend, not an Elasticsearch equivalence claim."""
    if not documents:
        return []
    frequencies = [Counter(doc) for doc in documents]
    df = Counter(word for doc in frequencies for word in doc)
    average = sum(map(len, documents)) / len(documents) or 1
    scores = []
    for doc, freq in zip(documents, frequencies):
        score = 0.0
        for word in set(query):
            count = freq.get(word, 0)
            if count:
                idf = math.log(1 + (len(documents) - df[word] + .5) / (df[word] + .5))
                score += idf * count * 2.2 / (count + 1.2 * (.25 + .75 * len(doc) / average))
        scores.append(score)
    return scores


@dataclass(frozen=True)
class ArticleMetadata:
    article_id: str
    title: str
    kind: str
    primary_entity: str = ""

    @classmethod
    def from_title(cls, article_id: str, title: str):
        clean = unescape(_TAGS.sub("", title)).strip()
        match = _DRUG_TITLE.fullmatch(clean)
        if not match:
            kind = "clinical_topic"
            if clean.casefold().startswith("patient education:"):
                kind = "patient_topic"
            elif clean.casefold().startswith(("society guideline links:", "calculator:")):
                kind = "navigation_topic"
            return cls(str(article_id), clean, kind)
        audience = (match[2] or "general").casefold()
        return cls(str(article_id), clean, "drug_" + audience, normalize(match[1]))


@dataclass(frozen=True)
class QueryPlan:
    entities: tuple[str, ...]
    query_terms: tuple[str, ...]
    section_terms: tuple[str, ...]
    facets: frozenset[str]
    population: str
    cross_topic: bool
    subject_groups: tuple[tuple[str, ...], ...] = ()
    intent: str = "general"
    search_text: str = ""


@dataclass(frozen=True)
class ArticleCandidate:
    article: ArticleMetadata
    reason: str


class ArticleCatalog:
    """Complete title catalog; never populated from retrieved paragraph hits."""

    def __init__(self, articles, *, aliases=None):
        self.articles = tuple(sorted(articles, key=lambda a: a.article_id))
        if len({a.article_id for a in self.articles}) != len(self.articles):
            raise ValueError("Duplicate article IDs in catalog")
        self.by_entity = defaultdict(list)
        self.postings = defaultdict(set)
        for index, article in enumerate(self.articles):
            if article.primary_entity:
                self.by_entity[article.primary_entity].append(article)
            for word in set(terms(article.title)):
                self.postings[word].add(index)
        self.aliases = {entity: entity for entity in self.by_entity}
        dictionary = SEED_ALIASES if aliases is None else aliases
        if not isinstance(dictionary, dict):
            raise ValueError("Entity aliases must be an object of name lists")
        for entity, names in dictionary.items():
            if not isinstance(entity, str) or not isinstance(names, (list, tuple)) or any(not isinstance(n, str) for n in names):
                raise ValueError("Entity aliases must map canonical names to name lists")
            entity = normalize(entity)
            if entity not in self.by_entity:
                continue
            for name in names:
                alias = normalize(name)
                if not alias or (alias in self.aliases and self.aliases[alias] != entity):
                    raise ValueError("Empty or ambiguous entity alias")
                self.aliases[alias] = entity
        # Index alias first words instead of scanning every drug for each query.
        self.alias_starts = defaultdict(list)
        for alias, entity in self.aliases.items():
            self.alias_starts[alias.split()[0]].append((tuple(alias.split()), entity))

    def plan(self, query: str, *, subjects=(), intent=None) -> QueryPlan:
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError("Expected a nonempty query of at most 2000 characters")
        words = normalize(query).split()
        entities, expanded = [], []
        position = 0
        while position < len(words):
            matches = [(alias, entity) for alias, entity in self.alias_starts.get(words[position], ())
                       if tuple(words[position:position + len(alias)]) == alias]
            if matches:
                alias, entity = max(matches, key=lambda item: len(item[0]))
                if entity not in entities:
                    entities.append(entity)
                expanded.extend(entity.split())
                position += len(alias)
            else:
                expanded.append(words[position])
                position += 1
        query_terms = terms(" ".join(expanded))
        populations = set(query_terms) & {"pediatric", "adult"}
        population = "mixed" if len(populations) == 2 else next(iter(populations), "unspecified")
        entity_terms = {word for entity in entities for word in terms(entity)}
        section_terms = tuple(word for word in query_terms if word not in entity_terms)
        if intent is None:
            intent = ("interaction" if "interaction" in query_terms else
                      "dosing" if set(query_terms) & {"dose", "adjust"} else
                      "diagnosis" if "diagnosis" in query_terms else
                      "prevention" if "prevention" in query_terms else
                      "management" if "management" in query_terms else "general")
        groups = tuple(tuple(word for word in terms(subject) if word not in _GENERIC)
                       for subject in subjects)
        groups = tuple(group for group in groups if group)
        if not groups:
            groups = tuple(tuple(terms(entity)) for entity in entities)
        if not groups:
            anchors = {word for word in query_terms if word not in _GENERIC and not word.isdecimal()}
            # Prefer a named subject over a generic intent even when the latter
            # has a high lexical score (insulin adjustment != adjustment disorder).
            known = [word for word in anchors if self.postings.get(word)]
            named = set(known) & _NAMED_SUBJECTS
            if named:
                known = sorted(named)
            if known:
                groups = ((min(known, key=lambda word: (len(self.postings[word]), word)),),)
            elif anchors:
                groups = ((sorted(anchors)[0],),)
        return QueryPlan(tuple(entities), query_terms, section_terms, frozenset(query_terms) & _FACETS,
                         population, bool(set(query_terms) & {"interaction", "compare"}) or len(entities) > 1,
                         groups, intent, query)

    def select(self, plan: QueryPlan, *, beam: int = 3) -> tuple[ArticleCandidate, ...]:
        if not 1 <= beam <= 10:
            raise ValueError("Article beam must be between 1 and 10")
        selected = []
        for entity in plan.entities:
            kinds = {"drug_pediatric"} if plan.population == "pediatric" else {"drug_general"}
            if plan.population == "mixed":
                kinds.add("drug_pediatric")
            if "patient" in plan.query_terms and not plan.facets:
                kinds = {"drug_patient"}
            for article in self.by_entity[entity]:
                if article.kind in kinds:
                    selected.append(ArticleCandidate(article, "exact_primary_entity_and_article_type"))
        clinical_intent = plan.intent in {"management", "diagnosis", "prevention", "adverse_effect"}
        if selected and not plan.cross_topic and not clinical_intent:
            return tuple(selected)
        related = set().union(*(_RELATED_SUBJECTS.get(word, set())
                               for group in plan.subject_groups for word in group))
        search_terms = set(plan.query_terms) | related
        candidates = set().union(*(self.postings.get(word, set()) for word in search_terms))
        candidates = sorted(candidates)
        articles = [self.articles[index] for index in candidates if self.articles[index].kind in
                    ({"clinical_topic", "patient_topic"} if "patient" in plan.query_terms and not plan.facets
                     else {"clinical_topic"})]
        if plan.entities and not clinical_intent:
            entity_terms = {word for entity in plan.entities for word in terms(entity)}
            context = set(plan.query_terms) - entity_terms - _FACETS - {
                "adjust", "impairment", "disease", "treatment", "therapy", "management",
                "compare", "pediatric", "adult", "patient",
            }
            if context:
                # A query about HIV interactions must retain HIV as a topic
                # anchor. A generic "interactions" title is insufficient.
                articles = [a for a in articles if context.issubset(set(terms(a.title)))]
            else:
                articles = [a for a in articles if any(
                    set(terms(entity)).issubset(set(terms(a.title))) for entity in plan.entities)]
            if "interaction" in plan.facets:
                articles = [a for a in articles if "interaction" in terms(a.title)]
        elif plan.subject_groups:
            def matches_subject(group, title_terms):
                return set(group).issubset(title_terms) or (
                    len(group) == 1 and bool(_RELATED_SUBJECTS.get(group[0], set()) & title_terms))
            articles = [a for a in articles if all(matches_subject(group, set(terms(a.title)))
                                                  for group in plan.subject_groups)]
        else:
            # Intent words alone do not identify an article.
            articles = []
        context_facets = plan.facets & {"kidney", "liver", "pregnancy"}
        if context_facets and not plan.entities:
            articles = [a for a in articles if context_facets.issubset(set(terms(a.title)))]
        if plan.population in {"adult", "pediatric"}:
            opposite = "pediatric" if plan.population == "adult" else "adult"
            articles = [a for a in articles if opposite not in terms(a.title)
                        or plan.population in terms(a.title)]
        scores = lexical_scores(tuple(search_terms), [terms(a.title) for a in articles])
        intent_term = {"dosing": "dose", "interaction": "interaction", "diagnosis": "diagnosis",
                       "management": "management", "prevention": "prevention"}.get(plan.intent)
        scores = [score * (1.5 if intent_term in terms(article.title) else 1)
                  for article, score in zip(articles, scores)]
        ranked = sorted(zip(articles, scores), key=lambda pair: (-pair[1], pair[0].article_id))
        topics = [ArticleCandidate(a, "title_only_topic_candidate") for a, score in ranked[:beam] if score > 0]
        # Preserve a monograph for every recognized entity in comparisons.
        # Cross-topic questions also retain title-selected clinical candidates.
        return tuple(topics + selected if clinical_intent else selected + topics)


@dataclass(frozen=True)
class Section:
    section_id: str
    title: str
    path_ids: tuple[str, ...]
    path_titles: tuple[str, ...]
    provenance: str


class _OutlineParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active = None
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "ul":
            self.depth += 1
        if tag == "a":
            match = re.search(r"sectionName\s*:\s*['\"]([^'\"]+)['\"]", attrs.get("onclick", ""))
            section_id = match[1] if match else ""
            if not section_id and attrs.get("href", "").startswith("#"):
                section_id = attrs["href"][1:]
            if section_id:
                self.active = [section_id, max(self.depth - 1, 0), []]

    def handle_data(self, data):
        if self.active is not None:
            self.active[2].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.active is not None:
            section_id, depth, pieces = self.active
            title = re.sub(r"^[-–—•]\s+", "", " ".join("".join(pieces).split()))
            if title and section_id.casefold() not in {"reference", "references"}:
                self.nodes.append((section_id, title, depth))
            self.active = None
        if tag == "ul":
            self.depth = max(0, self.depth - 1)


def article_sections(outline_html: str, article: ExtractedArticle) -> tuple[Section, ...]:
    parser = _OutlineParser()
    parser.feed(outline_html)
    parser.close()
    last = {node[0]: index for index, node in enumerate(parser.nodes)}
    sections, parents = {}, []
    for index, (section_id, title, depth) in enumerate(parser.nodes):
        if last[section_id] != index:
            continue
        while parents and parents[-1][0] >= depth:
            parents.pop()
        sections[section_id] = Section(section_id, title,
            tuple(p[1] for p in parents) + (section_id,),
            tuple(p[2] for p in parents) + (title,), "outline")
        parents.append((depth, section_id, title))
    used = {block.section_id for block in article.blocks}
    for block in article.blocks:
        if block.section_id not in sections:
            # Unknown ancestry stays flat and explicit; do not invent parents.
            sections[block.section_id] = Section(block.section_id, block.section_title,
                (block.section_id,), (block.section_title,), "body_heading_only" if block.section_id else "unsectioned")
    return tuple(section for section in sections.values()
                 if any(section.section_id in sections[leaf].path_ids for leaf in used))


@dataclass(frozen=True)
class PassageScope:
    article_id: str
    content_hash: str
    extraction_version: str
    section_ids: tuple[str, ...] | None
    paragraph_ids: tuple[str, ...] | None = None

    def validate(self):
        if not self.article_id or not self.content_hash or not self.extraction_version:
            raise ValueError("A versioned article scope is mandatory")
        if self.section_ids is not None and not self.section_ids:
            raise ValueError("Empty section scopes must not become global searches")
        if self.paragraph_ids is not None and not self.paragraph_ids:
            raise ValueError("Empty paragraph scopes must not become unrestricted searches")


def _population_matches(plan: QueryPlan, section: Section) -> bool:
    heading_terms = set(terms(" ".join(section.path_titles)))
    if plan.population == "pediatric" and "adult" in heading_terms and "pediatric" not in heading_terms:
        return False
    if plan.population in {"adult", "unspecified"} and "pediatric" in heading_terms and "adult" not in heading_terms:
        return False
    return True


def _useful_section(plan: QueryPlan, section: Section) -> bool:
    title = normalize(section.title)
    boilerplate = ("society guideline links", "acknowledgment", "references", "related topics")
    if any(title.startswith(label) for label in boilerplate):
        return False
    return "patient" in plan.query_terms or not title.startswith("information for patients")


def select_sections(plan: QueryPlan, sections: tuple[Section, ...], *, beam: int = 2,
                    article_title: str = ""):
    eligible = []
    # A condition explicit in the article title is inherited context. Requiring
    # it again in every child heading would exclude, e.g., pregnancy treatment.
    required_facets = plan.facets - set(terms(article_title))
    for section in sections:
        if not _population_matches(plan, section) or not _useful_section(plan, section):
            continue
        heading_terms = set(terms(" ".join(section.path_titles)))
        if required_facets and not required_facets.issubset(heading_terms):
            continue
        eligible.append(section)
    scores = lexical_scores(plan.section_terms, [terms(" ".join(s.path_titles)) for s in eligible])
    ranked = sorted(zip(eligible, scores), key=lambda pair: (-pair[1], -len(pair[0].path_ids), pair[0].section_id))
    selected = []
    for section, score in ranked:
        if score <= 0:
            continue
        if any(section.section_id in other.path_ids or other.section_id in section.path_ids for other in selected):
            continue
        selected.append(section)
        if len(selected) == beam:
            break
    return tuple(selected)


def local_passages(plan: QueryPlan, article: ExtractedArticle, scope: PassageScope, limit: int):
    scope.validate()
    if (article.content_id, article.content_hash, article.version) != (scope.article_id, scope.content_hash, scope.extraction_version):
        raise ValueError("Passage scope does not match article revision")
    blocks = [b for b in article.blocks
              if (scope.section_ids is None or b.section_id in scope.section_ids)
              and (scope.paragraph_ids is None or b.paragraph_id in scope.paragraph_ids)]
    # Titles choose articles/sections; paragraph scores must come from passages.
    scores = lexical_scores(plan.query_terms, [terms(b.text + " " + " ".join(b.table_headers)) for b in blocks])
    ranked = sorted(zip(blocks, scores), key=lambda pair: (-pair[1], pair[0].paragraph_id))
    return [{"article_id": article.content_id, "content_hash": article.content_hash,
             "extraction_version": article.version, "paragraph_id": b.paragraph_id,
             "section_id": b.section_id, "score": score, "table_context_status": b.table_context_status}
            for b, score in ranked[:limit] if score > 0 or scope.paragraph_ids is not None]


class HierarchicalRetriever:
    def __init__(self, catalog: ArticleCatalog, load_article: Callable, passage_search=local_passages):
        self.catalog = catalog
        self.load_article = load_article
        self.passage_search = passage_search

    def search(self, query: str, *, article_beam: int = 3, section_beam: int = 2, limit: int = 10):
        if not 1 <= section_beam <= 10 or not 1 <= limit <= 50:
            raise ValueError("Invalid section beam or passage limit")
        from .search_request import search_request
        return search_request(self, self.catalog.plan(query), original=query,
                              article_beam=article_beam, section_beam=section_beam, limit=limit)
