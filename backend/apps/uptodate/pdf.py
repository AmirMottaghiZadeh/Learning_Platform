"""PDF from the licensed local article, with local graphics only."""
import base64
from html import escape
import re
from bs4 import BeautifulSoup
from . import services
from .media import graphic_ids, safe_fragment


def article_pdf(article):
    from weasyprint import HTML
    from weasyprint.urls import URLFetcher, URLFetcherResponse

    class LocalImages(URLFetcher):
        def fetch(self,url,headers=None):
            match=re.fullmatch(r"https://pharmenta.invalid/utd-image/([A-Za-z0-9_.-]{1,100})",url)
            if not match:raise ValueError("Only local reference images are allowed.")
            image=services.get_image(match[1])
            if image is None:raise ValueError("Local image is unavailable.")
            return URLFetcherResponse(url,base64.b64decode(image["data_base64"]),{"Content-Type":image["content_type"]})

    def clean(body, prefix=""):
        soup=BeautifulSoup(safe_fragment(body),"html.parser")
        if prefix:
            for node in soup.find_all(id=True):node["id"]=prefix+node["id"]
            for link in soup.find_all("a",href=True):
                if link["href"].startswith("#"):link["href"]="#"+prefix+link["href"][1:]
        for image in soup.find_all("img"):
            identifier=image.get("src","")
            if identifier:image["src"]="https://pharmenta.invalid/utd-image/"+identifier
            else:image.decompose()
        return str(soup)

    body=clean(article["body_html"])
    appendix=[]
    for identifier in graphic_ids(article["body_html"]):
        graphic=services.get_topic(identifier)
        if graphic:
            appendix.append(f'<section class="graphic" id="graphic-{identifier}"><h2>{escape(graphic["title"])}</h2>{clean(graphic["body_html"],prefix="g"+identifier+"-")}</section>')
    css="""@page {size:A4; margin:18mm 15mm; @bottom-right {content:counter(page);font-size:9pt;color:#5f6b68}}
    body{font:10pt/1.55 'DejaVu Sans',sans-serif;color:#14201d}h1{font-size:20pt;color:#0f5c52}h2{font-size:14pt;color:#0f5c52}h3{font-size:12pt}
    table{border-collapse:collapse;width:100%;font-size:8pt}td,th{border:1px solid #cbd6d0;padding:5pt;overflow-wrap:anywhere}th{background:#eef4f0}thead{display:table-header-group}tr{break-inside:avoid}
    img{max-width:100%;max-height:240mm;object-fit:contain}a{color:#0f5c52;text-decoration:none}p{orphans:3;widows:3}.graphic{break-before:page}.meta{font-size:9pt;color:#5f6b68;border-bottom:1px solid #cbd6d0;padding-bottom:12pt}
    """
    html=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{escape(article["title"])}</title><style>{css}</style></head><body><h1>{escape(article["title"])}</h1><p class="meta">UpToDate · {escape(article.get("updated", ""))} · Pharmenta</p>{body}{"".join(appendix)}</body></html>'
    return HTML(string=html,url_fetcher=LocalImages(allow_redirects=False)).write_pdf()
