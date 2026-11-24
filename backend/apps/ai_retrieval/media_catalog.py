"""One-pass metadata extraction; keep rich HTML parsing out of full-corpus indexing."""
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import re
from apps.uptodate import services
from apps.uptodate.media_links import media_links


class Probe(HTMLParser):
    def __init__(self,identifier,title):
        super().__init__(convert_charrefs=True)
        self.identifier,self.title=identifier,title
        self.ordinal=0;self.depth=0;self.table=None;self.records=[];self.text=[];self.skip=0

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in {"script","style","noscript"}:self.skip+=1
        if self.skip:return
        if tag in {"table","img"}:
            ordinal=self.ordinal;self.ordinal+=1
            if tag=="table":
                self.depth+=1
                if self.depth==1:self.table={"ordinal":ordinal,"parts":[],"caption":[],"in_caption":False,"shape":[]}
            elif self.depth==0 and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",attrs.get("src","")):
                caption=attrs.get("alt","") or attrs.get("title","")
                self.records.append(self.record("image",ordinal,caption or self.title,caption,caption or self.title,
                                                "image:" + attrs["src"]))
        if self.table:
            if tag=="caption":self.table["in_caption"]=True
            if tag in {"td","th","tr","p","br"}:self.table["parts"].append(" ")
            if tag in {"table", "tr", "th", "td", "caption"}:
                self.table["shape"].append(f"<{tag}:{attrs.get('rowspan') or '1'}:{attrs.get('colspan') or '1'}>")
            if tag == "img":
                self.table["shape"].append(f"<image:{attrs.get('src') or ''}>")

    def handle_data(self,data):
        if self.skip:return
        self.text.append(data)
        if self.table:
            self.table["parts"].append(data)
            self.table["shape"].append(data)
            if self.table["in_caption"]:self.table["caption"].append(data)

    def handle_endtag(self,tag):
        if tag in {"script","style","noscript"} and self.skip:self.skip-=1;return
        if self.skip:return
        if self.table and tag=="caption":self.table["in_caption"]=False
        if self.table and tag in {"table", "tr", "th", "td", "caption"}:
            self.table["shape"].append(f"</{tag}>")
        if tag=="table" and self.depth:
            self.depth-=1
            if self.depth==0 and self.table:
                table=self.table;self.table=None
                caption=" ".join("".join(table["caption"]).split())
                shape = re.sub(r">\s+<", "><", " ".join("".join(table["shape"]).split()))
                self.records.append(self.record("table",table["ordinal"],caption or self.title,caption,
                    " ".join("".join(table["parts"]).split()),"table:" + sha256(shape.encode()).hexdigest()))

    def record(self,kind,ordinal,title,caption,text,asset_id):
        key="um-"+sha256(f"{self.identifier}:{kind}:{ordinal}".encode()).hexdigest()[:32]
        return {"key":key,"kind":kind,"title":title,"caption":caption,"text":text,"asset_id":asset_id}


def probe(article):
    parser=Probe(article["id"],article["title"]);parser.feed(article["body_html"]);parser.close()
    return parser


@lru_cache(maxsize=256)
def graphic_records(identifier,version):
    article=services.get_topic(identifier,include_memberships=False)
    if article is None:return []
    parser=probe(article);description=" ".join(" ".join(parser.text).split())
    return [{**item,"title":article["title"],"caption":item["caption"] or article["title"],"text":description,
             "graphic_hash":sha256(article["body_html"].encode()).hexdigest()} for item in parser.records]


def catalog_media(article, *, links=None):
    records = list(probe(article).records)
    if links is None:
        links = [*media_links(article["body_html"]), *media_links(article.get("outline_html", ""))]
    grouped = {}
    for link in links:
        if link.graphic and link.identifier != str(article["id"]):
            grouped.setdefault(link.identifier, []).append(link)
    for identifier, locations in grouped.items():
        labels = list(dict.fromkeys(link.label for link in locations if link.label))
        groups = list(dict.fromkeys(link.group for link in locations if link.group))
        context = list(dict.fromkeys(link.context for link in locations if link.context))
        for child in graphic_records(identifier, services.snapshot_version()):
            records.append({**child, "key": f"graphic-{identifier}-{child['key']}",
                            "source_labels": labels, "source_groups": groups, "source_context": context})
    return records


def initialize_worker():
    import django
    django.setup()
