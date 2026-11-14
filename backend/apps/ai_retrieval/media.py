"""Caption/table search alongside existing vectors; no new paid embedding."""
import re
from django.contrib.postgres.search import SearchQuery,SearchRank,SearchVector
from apps.ai_lab.retrieval import Passage
from apps.uptodate.search_catalog import normalize
from .models import ReferenceMedia


def requested(question):
    return bool(re.search(r"جدول|تصویر|عکس|نمودار|فلوچارت|الگوریتم|\b(?:tables?|figures?|images?|illustrations?|flowcharts?)\b",question,re.I)
        or re.search(r"شکل(?!\s*دارویی)",question))


def requested_kinds(question):
    table=bool(re.search(r"جدول|\btables?\b",question,re.I))
    image=bool(re.search(r"تصویر|عکس|شکل(?!\s*دارویی)|\b(?:figures?|images?|pictures?|illustrations?)\b",question,re.I))
    return {"table","image"} if table==image else {"table"} if table else {"image"}


def search(generation,query,*,article_ids=(),audience="general",limit=3,kinds=None):
    kinds=kinds or requested_kinds(query)
    skip={"show","find","display","table","tables","figure","figures","image","images","picture","pictures","please","give","chart","diagram"}
    terms=[word for word in normalize(query).split() if word not in skip and len(word)>2][:12]
    if not terms:return []
    aspects={"initial","management","treatment","children","child","pediatric","paediatric","adult","adults","patient","patients",
             "overview","evaluation","clinical","recommended","first","line","approach","algorithm"}
    topic=[word for word in terms if word not in aspects] or terms
    query=SearchQuery(" OR ".join(terms),config="english",search_type="websearch")
    rows=ReferenceMedia.objects.filter(generation=generation).annotate(document=SearchVector("search_text",config="english"))
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
        descriptor={**row.descriptor,"key":row.media_key,"kind":row.kind,"title":row.title,
            "caption":row.caption[:1500],"article_id":row.source_id,"content_hash":row.content_hash}
        result.append(Passage("M"+str(row.pk),row.source_id,row.article_title,row.title,row.evidence_text,
            {"screen":"uptodateArticle","params":{"id":row.source_id,"title":row.article_title,"mediaKey":row.media_key,
                "mediaContentHash":row.content_hash,"mediaGraphicHash":row.descriptor.get("graphic_hash","")}},
            row.content_hash,heading_path=(row.title,),media=(descriptor,)))
        if len(result)>=limit:break
    return result
