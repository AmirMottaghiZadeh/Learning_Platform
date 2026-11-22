"""Caption/table search alongside existing vectors; no new paid embedding."""
import re
from hashlib import sha256
from django.contrib.postgres.search import SearchQuery,SearchRank,SearchVector
from apps.ai_lab.retrieval import Passage
from apps.uptodate.search_catalog import normalize
from .models import ReferenceMedia

MEDIA_ASPECTS = {"initial", "management", "treatment", "children", "child", "pediatric", "paediatric",
                 "adult", "adults", "patient", "patients", "overview", "evaluation", "clinical",
                 "recommended", "first", "line", "approach", "algorithm", "dose", "dosing"}


def requested(question):
    return bool(re.search(r"جدول|تصویر|عکس|نمودار|فلوچارت|الگوریتم|\b(?:tables?|figures?|images?|illustrations?|flowcharts?)\b",question,re.I)
        or re.search(r"شکل(?!\s*دارویی)",question))


def requested_kinds(question):
    table=bool(re.search(r"جدول|\btables?\b",question,re.I))
    image=bool(re.search(r"تصویر|عکس|شکل(?!\s*دارویی)|\b(?:figures?|images?|pictures?|illustrations?)\b",question,re.I))
    return {"table","image"} if table==image else {"table"} if table else {"image"}


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


def outline_media(articles, queries, question, audience, limit=6):
    from apps.uptodate import services
    from . import media_catalog
    from .chunking import source_metadata

    kinds = requested_kinds(question)
    terms = {word for word in normalize(" ".join(queries)).split() if len(word) > 2} - MEDIA_ASPECTS
    if not terms:
        return []
    ranked = []
    for article in articles:
        raw = services.get_topic(article.source_id, include_memberships=False)
        if not raw or sha256(raw["body_html"].encode()).hexdigest() != article.content_hash:
            continue
        for record in media_catalog.catalog_media(raw):
            media_audience, _ = source_metadata(article.title, [record["title"], record["caption"]])
            if record["kind"] not in kinds or {audience, media_audience} == {"adult", "pediatric"}:
                continue
            own_title = normalize(f'{record["title"]} {record["caption"]}') if record["title"] != article.title or record["caption"] else ""
            own_body = normalize(record["text"]) if record["text"] != article.title else ""
            hits = len(terms.intersection(own_title.split()))
            body_hits = len(terms.intersection(own_body.split()))
            if not hits and not body_hits:
                continue
            complete = len(record["text"]) <= 12000
            body = record["text"] if complete else record["caption"] or record["title"]
            text = "\n".join(dict.fromkeys(filter(None, (record["title"], record["caption"], body))))
            key = sha256(f'{article.source_id}:{record["key"]}'.encode()).hexdigest()[:24]
            descriptor = {**record, "content_complete": complete}
            descriptor.pop("text")
            ranked.append((hits * 2 + body_hits, media_passage("M" + key, article.source_id, article.title,
                          article.content_hash, descriptor, text)))
    return [item for _, item in sorted(ranked, key=lambda entry: entry[0], reverse=True)[:limit]]


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
        result.append(passage(row))
        if len(result)>=limit:break
    return result
