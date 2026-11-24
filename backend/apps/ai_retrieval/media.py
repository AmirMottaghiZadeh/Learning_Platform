"""Caption/table search alongside existing vectors; no new paid embedding."""
import re
from hashlib import sha256
from django.contrib.postgres.search import SearchQuery,SearchRank,SearchVector
from apps.ai_lab.retrieval import Passage
from apps.billing.enforcement import require_feature
from apps.core.exceptions import PlatformAPIError
from apps.uptodate.search_catalog import normalize
from .models import ReferenceMedia

MEDIA_ASPECTS = {"initial", "management", "treatment", "children", "child", "pediatric", "paediatric",
                 "adult", "adults", "patient", "patients", "overview", "evaluation", "clinical",
                 "recommended", "first", "line", "approach", "algorithm", "dose", "dosing"}


TABLE_INTENT = re.compile(r"(?<![آ-ی])جدول|\btables?\b", re.I)
IMAGE_INTENT = re.compile(
    r"(?<![آ-ی])(?:تصویر|عکس|نمودار|شکل(?![\s‌-]*دارویی))|\b(?:figures?|images?|pictures?|illustrations?|diagrams?)\b", re.I)
ALGORITHM_INTENT = re.compile(r"(?<![آ-ی])(?:الگوریتم|فلو[\s‌-]*چارت)|\b(?:algorithms?|flow[ -]?charts?|decision trees?)\b", re.I)
LOOKUP_WORDS = set("show find display table tables figure figures image images picture pictures please give chart diagram text reference original article".split())


def requested(question):
    return any(pattern.search(question) for pattern in (TABLE_INTENT, IMAGE_INTENT, ALGORITHM_INTENT))


def requested_kinds(question):
    kinds = {kind for kind, pattern in (("table", TABLE_INTENT), ("image", IMAGE_INTENT)) if pattern.search(question)}
    return kinds or {"table", "image"}


def requested_types(question):
    return [kind for kind, pattern in (("algorithm", ALGORITHM_INTENT), ("table", TABLE_INTENT),
                                       ("image", IMAGE_INTENT)) if pattern.search(question)]


def catalog_query(query):
    if not requested(query):
        return query
    value = query
    for pattern in (TABLE_INTENT, IMAGE_INTENT, ALGORITHM_INTENT):
        value = pattern.sub(" ", value)
    words = [word for word in value.split() if word.lower() not in LOOKUP_WORDS | {"for", "of", "the", "a", "and"}]
    return " ".join(words) or query


def passage(row):
    return media_passage("M"+str(row.pk), row.source_id, row.article_title, row.content_hash,
        {**row.descriptor, "key": row.media_key, "kind": row.kind, "title": row.title, "caption": row.caption},
        row.evidence_text)


def media_passage(identifier, article_id, article_title, content_hash, record, text):
    descriptor = {**record, "caption": record["caption"][:1500], "article_id": article_id, "content_hash": content_hash}
    return Passage(identifier, article_id, article_title, record["title"], text,
        {"screen": "uptodateArticle", "params": {"id": article_id, "title": article_title, "mediaKey": record["key"],
         "mediaContentHash": content_hash, "mediaGraphicHash": record.get("graphic_hash", "")}},
        content_hash, heading_path=(record["title"],), media=(descriptor,))


def target_identity(asset):
    key = asset["key"]
    return key if key.startswith("graphic-") else f'{asset["article_id"]}:{key}'


def identity(asset):
    """A source file or table can be cited through multiple parent articles."""
    return asset.get("asset_id") or target_identity(asset)


def _passage_from_record(article, record):
    complete = len(record["text"]) <= 12000
    body = record["text"] if complete else record["caption"] or record["title"]
    text = "\n".join(dict.fromkeys(filter(None, (record["title"], record["caption"], body))))
    key = sha256(f'{article.source_id}:{record["key"]}'.encode()).hexdigest()[:24]
    descriptor = {name: record[name] for name in ("key", "kind", "title", "caption", "graphic_hash", "source_labels", "asset_id") if name in record}
    return media_passage("M" + key, article.source_id, article.title, article.content_hash,
                         {**descriptor, "content_complete": complete, "is_algorithm": _algorithm(record)}, text)


def _algorithm(record):
    return bool(ALGORITHM_INTENT.search(" ".join([record["title"], record.get("caption", ""),
        *record.get("source_labels", []), *record.get("source_groups", [])])))


def _number_matches(question, record):
    western_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    prefixes = {"table": r"table|جدول", "image": r"fig\.?|figure|image|شکل|تصویر"}
    prefix = prefixes.get(record.get("kind"), "|".join(prefixes.values()))
    pattern = rf"(?:{prefix})\s*(?:شماره\s*|#\s*)?(\d+)"
    numbers = re.findall(pattern, question.translate(western_digits), re.I)
    if not numbers:
        return True
    labels = " ".join([record["title"], record.get("caption", ""), *record.get("source_labels", [])])
    return bool(set(numbers).intersection(re.findall(pattern, labels.translate(western_digits), re.I)))


def outline_media(articles, queries, question, audience, limit=6, *, request=None, generation_id=None,
                  allow_related=lambda _parent, _target: True):
    from apps.ai_lab.models import ReferenceArticle
    from apps.uptodate import services
    from apps.uptodate.media_links import media_links
    from . import media_catalog
    from .chunking import source_metadata

    kinds = requested_kinds(question)
    explicit = requested(question)
    wants_algorithm = bool(ALGORITHM_INTENT.search(question))
    media_only_algorithm = wants_algorithm and not (TABLE_INTENT.search(question) or IMAGE_INTENT.search(question))
    terms = set(normalize(" ".join(queries)).split()) - LOOKUP_WORDS
    topic = {word for word in terms - MEDIA_ASPECTS if len(word) > 2}
    if not topic and not explicit:
        return []
    ranked, related, inspected = [], {}, set()

    def matches(text):
        return topic.intersection(normalize(text).split())

    def inspect(article, origin_label="", parent=""):
        if article.source_id in inspected:
            return
        inspected.add(article.source_id)
        try:
            require_feature(request, "uptodate", item=article.source_id, consume=False)
        except PlatformAPIError:
            return
        raw = services.get_topic(article.source_id, include_memberships=False)
        if not raw or sha256(raw["body_html"].encode()).hexdigest() != article.content_hash:
            return
        links = []
        if explicit:
            links = [*media_links(raw["body_html"]), *media_links(raw.get("outline_html", ""))]
            if not parent:
                for link in links:
                    relevant = matches(link.label) or matches(link.context) or (not link.context and matches(article.title))
                    if not link.graphic and link.identifier not in inspected and relevant:
                        related.setdefault(link.identifier, (article.source_id, link.label))
            # Prefer anchors whose labels or nearby prose answer the request.
            # A label such as "Table 1" is still genuine source evidence.
            def link_score(link):
                label = " ".join((link.label, link.group))
                return (wants_algorithm and bool(ALGORITHM_INTENT.search(label)), len(matches(label)),
                        len(matches(link.context)), _number_matches(question, {"title": label, "caption": ""}))
            links = sorted((link for link in links if link.graphic), key=link_score, reverse=True)
            wanted = list(dict.fromkeys(link.identifier for link in links))[:24]
            links = [link for link in links if link.identifier in wanted]
        for record in media_catalog.catalog_media(raw, links=links if explicit else None):
            label = " ".join([record["title"], record["caption"],
                              *record.get("source_labels", []), *record.get("source_groups", [])])
            media_audience, _ = source_metadata(article.title, [label])
            algorithm = _algorithm(record)
            if ((record["kind"] not in kinds and not (wants_algorithm and algorithm))
                    or (media_only_algorithm and not algorithm)
                    or {audience, media_audience} == {"adult", "pediatric"}
                    or not _number_matches(question, record)):
                continue
            own_title = label if record["title"] != article.title or record["caption"] else ""
            own_body = record["text"] if record["text"] != article.title else ""
            own = matches(own_title)
            nearby = matches(" ".join(record.get("source_context", [])))
            context = matches(own_body)
            domain = matches(article.title + " " + origin_label)
            if not own and not context and not (explicit and (nearby or domain or not topic)):
                continue
            aspect_hits = (terms & set(normalize(label + " " + own_body).split())) - topic
            score = 6 * len(own) + 3 * len(nearby) + 2 * len(context) + 2 * len(domain) + len(aspect_hits)
            if wants_algorithm and algorithm:
                score += 10
            ranked.append((score, parent, _passage_from_record(article, record)))

    for article in articles:
        inspect(article)
    if explicit and generation_id and related:
        identifiers = sorted(related, key=lambda identifier: -len(matches(related[identifier][1])))[:12]
        children = {article.source_id: article for article in ReferenceArticle.objects.filter(
            generation_id=generation_id, source_id__in=identifiers, is_directory=False)}
        for identifier in identifiers:
            if identifier in children:
                parent, label = related[identifier]
                inspect(children[identifier], label, parent)
    selected = []
    admitted = set()
    pending = sorted(ranked, key=lambda entry: entry[0], reverse=True)
    groups = requested_types(question)
    if len(groups) > 1:
        first = [next((entry for entry in pending if group in (entry[2].media[0]["kind"],
            "algorithm" if entry[2].media[0].get("is_algorithm") else "")), None) for group in groups]
        pending = [entry for entry in first if entry is not None] + pending
    for _, parent, item in pending:
        asset_id = identity(item.media[0])
        if asset_id in admitted or parent and not allow_related(parent, item.article_id):
            continue
        admitted.add(asset_id)
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def media_answer(question, passages):
    """Return factual discovery of an original asset without a generated availability claim."""
    from apps.ai_lab.hybrid_agent import _citation

    types = requested_types(question)
    def matches(passage):
        if not passage.media:
            return False
        asset = passage.media[0]
        algorithm = asset.get("is_algorithm") or _algorithm(asset)
        return (asset["kind"] in types or algorithm and "algorithm" in types) and _number_matches(question, asset)

    unique = {}
    for passage in passages:
        if matches(passage):
            unique.setdefault(identity(passage.media[0]), passage)
    rows = list(unique.values())[:6]
    if not rows:
        return {}
    assets = [row.media[0] for row in rows]
    kinds = {asset["kind"] for asset in assets}
    if any(asset.get("is_algorithm") or _algorithm(asset) for asset in assets):
        kinds.add("algorithm")
    complete = set(types) <= kinds
    items, blocks = [], []
    for passage, asset in zip(rows, assets):
        label = "الگوریتم" if asset.get("is_algorithm") or _algorithm(asset) else "جدول" if asset["kind"] == "table" else "تصویر"
        item = _citation(passage, retrieved=True)
        text = f"{label} اصلی در مقالهٔ مرجع پیدا شد."
        item["summary_fa"] = text
        items.append(item)
        blocks.append({"text_fa": text, "source_ids": [item["source_id"]]})
    return {"status": "answered" if complete else "partial", "items": items, "answer_blocks": blocks,
            "overview_fa": "\n\n".join(block["text_fa"] for block in blocks),
            "clarification_fa": "" if complete else "بخشی از رسانه‌های درخواستی در منابع بررسی‌شده پیدا شد."}


def citation_valid(citation):
    """Validate an original linked graphic/table without trusting model metadata."""
    from . import media_catalog
    from apps.uptodate import services
    try:
        params=citation["target"]["params"]
        if citation.get("source")!="uptodate" or citation["target"].get("screen")!="uptodateArticle":
            return False
        article=services.get_topic(params["id"],include_memberships=False)
        if article is None or sha256(article["body_html"].encode()).hexdigest()!=citation["content_hash"]:
            return False
        if params.get("mediaContentHash")!=citation["content_hash"]:
            return False
        record=next((r for r in media_catalog.catalog_media(article) if r["key"]==params["mediaKey"]),None)
        if record is None or record.get("graphic_hash","")!=params.get("mediaGraphicHash",""):
            return False
        match=re.match(r"graphic-(\d+)-",record["key"])
        if match:
            graphic=services.get_topic(match[1],include_memberships=False)
            if graphic is None or sha256(graphic["body_html"].encode()).hexdigest()!=record.get("graphic_hash"):
                return False
        complete=len(record["text"])<=12000
        text=record["text"] if complete else record["caption"] or record["title"]
        expected="\n".join(dict.fromkeys(filter(None,[record["title"],record["caption"],text])))
        return citation.get("quote")==expected and bool(citation.get("media")) and all(
            item.get("key")==record["key"] and item.get("article_id")==str(params["id"])
            and (not item.get("asset_id") or item["asset_id"] == record["asset_id"])
            and item.get("content_hash")==citation["content_hash"] and item.get("kind")==record["kind"]
            and item.get("content_complete")==complete for item in citation.get("media",[]))
    except (KeyError,TypeError,ValueError):
        return False


def search(generation,query,*,article_ids=(),audience="general",limit=3,kinds=None,scoped=False,implicit=False):
    kinds=kinds or requested_kinds(query)
    skip={"show","find","display","table","tables","figure","figures","image","images","picture","pictures","please","give","chart","diagram"}
    terms=[word for word in normalize(query).split() if word not in skip and len(word)>2][:12]
    if not terms:return []
    topic=[word for word in terms if word not in MEDIA_ASPECTS] or terms
    query=SearchQuery(" OR ".join(terms),config="english",search_type="websearch")
    rows=ReferenceMedia.objects.filter(generation=generation).annotate(document=SearchVector("search_text",config="english"))
    if scoped:
        rows=rows.filter(source_id__in=article_ids)
    rows=rows.filter(kind__in=kinds)
    if audience=="pediatric":rows=rows.exclude(audience="adult")
    elif audience=="adult":rows=rows.exclude(audience="pediatric")
    topic_query=SearchQuery(" OR ".join(topic),config="english",search_type="websearch")
    candidates=list(rows.filter(document=topic_query).annotate(rank=SearchRank(SearchVector("search_text",config="english"),query)).order_by("-rank")[:40])
    def rank(row):
        text=normalize(row.search_text);hits=sum(term in text for term in terms)
        title=normalize(f"{row.article_title} {row.title} {row.caption}")
        focus=sum(term in title for term in topic)/len(topic)
        return focus*2+hits/len(terms)+(0.25 if row.source_id in article_ids else 0),getattr(row,"rank",0)
    candidates.sort(key=rank,reverse=True)
    result=[]
    seen = set()
    for row in candidates:
        title=normalize(f"{row.article_title} {row.title} {row.caption}")
        if sum(term in title for term in topic)/len(topic)<0.5:continue
        if rank(row)[0]<min(0.6,2/len(terms)):continue
        if implicit:
            # The article title alone would match every figure in a topic.
            # Require evidence from the media's own caption, title or table.
            article_title = normalize(row.article_title)
            content = " ".join(normalize(part) for part in (row.title, row.caption, *row.evidence_text.splitlines()[1:])
                               if normalize(part) != article_title)
            if not set(topic).intersection(content.split()):
                continue
        item = passage(row)
        asset_id = identity(item.media[0])
        if asset_id in seen:
            continue
        seen.add(asset_id)
        result.append(item)
        if len(result)>=limit:break
    return result
