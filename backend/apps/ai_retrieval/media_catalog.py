"""One-pass metadata extraction; keep rich HTML parsing out of full-corpus indexing."""
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import re
from apps.uptodate import services


class Probe(HTMLParser):
    def __init__(self,identifier,title):
        super().__init__(convert_charrefs=True)
        self.identifier,self.title=identifier,title
        self.ordinal=0;self.depth=0;self.table=None;self.records=[];self.graphics=[];self.text=[];self.skip=0

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in {"script","style","noscript"}:self.skip+=1
        if self.skip:return
        if tag=="a":
            match=re.search(r"[\"']?contentIds[\"']?\s*:\s*\[\s*[\"']([0-9]+)[\"']",attrs.get("onclick",""))
            if match:self.graphics.append(match[1])
        if tag in {"table","img"}:
            ordinal=self.ordinal;self.ordinal+=1
            if tag=="table":
                self.depth+=1
                if self.depth==1:self.table={"ordinal":ordinal,"parts":[],"caption":[],"in_caption":False}
            elif self.depth==0 and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",attrs.get("src","")):
                caption=attrs.get("alt","") or attrs.get("title","")
                self.records.append(self.record("image",ordinal,caption or self.title,caption,caption or self.title,attrs["src"]))
        if self.table:
            if tag=="caption":self.table["in_caption"]=True
            if tag in {"td","th","tr","p","br"}:self.table["parts"].append(" ")

    def handle_data(self,data):
        if self.skip:return
        self.text.append(data)
        if self.table:
            self.table["parts"].append(data)
            if self.table["in_caption"]:self.table["caption"].append(data)

    def handle_endtag(self,tag):
        if tag in {"script","style","noscript"} and self.skip:self.skip-=1;return
        if self.skip:return
        if self.table and tag=="caption":self.table["in_caption"]=False
        if tag=="table" and self.depth:
            self.depth-=1
            if self.depth==0 and self.table:
                table=self.table;self.table=None
                caption=" ".join("".join(table["caption"]).split())
                self.records.append(self.record("table",table["ordinal"],caption or self.title,caption,
                    " ".join("".join(table["parts"]).split()),""))

    def record(self,kind,ordinal,title,caption,text,image_id):
        key="um-"+sha256(f"{self.identifier}:{kind}:{ordinal}".encode()).hexdigest()[:32]
        return {"key":key,"kind":kind,"title":title,"caption":caption,"text":text,"image_id":image_id}


def probe(article):
    parser=Probe(article["id"],article["title"]);parser.feed(article["body_html"]);parser.close()
    outline=Probe(article["id"],article["title"]);outline.feed(article.get("outline_html",""));outline.close()
    return parser,list(dict.fromkeys([*parser.graphics,*outline.graphics]))


@lru_cache(maxsize=256)
def graphic_records(identifier,version):
    article=services.get_topic(identifier,include_memberships=False)
    if article is None:return []
    parser,_=probe(article);description=" ".join(" ".join(parser.text).split())
    return [{**item,"title":article["title"],"caption":item["caption"] or article["title"],"text":description,
             "graphic_hash":sha256(article["body_html"].encode()).hexdigest()} for item in parser.records]


def catalog_media(article):
    parser,graphics=probe(article)
    records=list(parser.records)
    for identifier in graphics:
        for child in graphic_records(identifier,services.snapshot_version()):
            records.append({**child,"key":f"graphic-{identifier}-{child['key']}"})
    return records


def initialize_worker():
    import django
    django.setup()
