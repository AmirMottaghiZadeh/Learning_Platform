"""Original local tables/figures. Stable keys, captions and safe viewer markup."""
from hashlib import sha256
from html import escape
import re
from bs4 import BeautifulSoup


def graphic_ids(html):
    soup=BeautifulSoup(html,"html.parser")
    return list(dict.fromkeys(match.group(1) for anchor in soup.find_all("a",onclick=True)
        if (match:=re.search(r"[\"']?contentIds[\"']?\s*:\s*\[\s*[\"']([0-9]+)[\"']",anchor["onclick"]))))


def safe_fragment(html):
    soup=BeautifulSoup(html,"html.parser")
    allowed={"div","p","span","br","b","strong","i","em","u","sub","sup","ul","ol","li","dl","dt","dd",
             "table","thead","tbody","tfoot","tr","th","td","caption","colgroup","col","h1","h2","h3","h4","h5","h6","blockquote","a","hr","img"}
    for node in list(soup.find_all(True)):
        if node.name in {"script","style","iframe","object","embed","form","input","button","link","meta","base","svg"}:
            node.decompose();continue
        if node.parent is None:continue
        if node.name not in allowed:
            node.unwrap();continue
        attrs={key:value for key,value in node.attrs.items() if key in {"id","alt","title","rowspan","colspan","scope","headers"}}
        if node.name=="a" and re.match(r"^(?:https://|#)",node.get("href", "")):
            attrs["href"]=node["href"]
        if node.name=="img" and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",node.get("src","")):
            attrs["src"]=node["src"]
        node.attrs=attrs
    return str(soup)


def extract_media(article, *, include_graphics=True):
    """Descriptors only; no image bytes or network request is needed."""
    body=article["body_html"];soup=BeautifulSoup(body,"html.parser");records=[]
    for ordinal,node in enumerate(soup.find_all(["table","img"])):
        if node.name=="table" and node.find_parent("table"):continue
        if node.name=="img" and node.find_parent("table"):continue
        kind="table" if node.name=="table" else "image"
        heading=node.find_previous(["h1","h2","h3","h4"])
        caption=node.find("caption") if kind=="table" else node.find_parent("figure")
        text=(caption.get_text(" ",strip=True) if caption else node.get("alt","") or node.get("title",""))
        title=text or article["title"]
        key="um-"+sha256(f"{article['id']}:{kind}:{ordinal}".encode()).hexdigest()[:32]
        identifier=node.get("src","") if kind=="image" else ""
        if kind=="image" and not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",identifier):continue
        records.append({"key":key,"kind":kind,"title":title,"caption":text,"heading":heading.get_text(" ",strip=True) if heading else "",
            "text":node.get_text(" ",strip=True) if kind=="table" else text or article["title"],
            "image_id":identifier,"html":safe_fragment(str(node)) if kind=="table" else "","ordinal":ordinal})
    if include_graphics:
        for identifier in graphic_ids(body+article.get("outline_html","")):
            records.append({"key":"graphic-"+identifier,"kind":"graphic","title":"","caption":"","heading":"",
                "text":"","image_id":"","html":"","ordinal":len(records),"graphic_id":identifier})
    return records


def resolved_media(article):
    from . import services
    result=[]
    for item in extract_media(article):
        if item["kind"]!="graphic":result.append(item);continue
        graphic=services.get_topic(item["graphic_id"])
        if graphic is None:continue
        description=BeautifulSoup(graphic["body_html"],"html.parser").get_text(" ",strip=True)
        for child in extract_media(graphic,include_graphics=False):
            result.append({**child,"key":item["key"]+"-"+child["key"],"title":graphic["title"],
                "caption":child["caption"] or graphic["title"],"graphic_id":graphic["id"],
                "text":description,
                "graphic_hash":sha256(graphic["body_html"].encode()).hexdigest(),"child_key":child["key"]})
    return result


def resolve_one(article,key):
    direct=next((item for item in extract_media(article,include_graphics=False) if item["key"]==key),None)
    if direct:return direct
    match=re.fullmatch(r"graphic-(\d+)-(um-[a-f0-9]{32})",key)
    if not match or match[1] not in graphic_ids(article["body_html"]+article.get("outline_html","")):return None
    from . import services
    graphic=services.get_topic(match[1])
    if graphic is None:return None
    child=next((item for item in extract_media(graphic,include_graphics=False) if item["key"]==match[2]),None)
    return {**child,"key":key,"title":graphic["title"],"graphic_hash":sha256(graphic["body_html"].encode()).hexdigest()} if child else None


def viewer_payload(item):
    if item["kind"]=="table":
        from . import services
        table=BeautifulSoup(item["html"],"html.parser")
        for node in table.find_all("img"):
            image=services.get_image(node.get("src",""))
            if image:node["src"]=f"data:{image['content_type']};base64,{image['data_base64']}"
            else:node.decompose()
        return {"kind":"table","html":str(table),"headers":None,"rows":[],"caption":item["title"]}
    from . import services
    image=services.get_image(item["image_id"])
    if image is None:return None
    return {"kind":"image","src":f"data:{image['content_type']};base64,{image['data_base64']}","alt":item["caption"],"caption":item["title"]}
