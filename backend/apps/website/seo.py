"""Structured data (schema.org JSON-LD) for the site's pages, and the stable
icon files search engines and phones ask for at the site root.

Built as Python dicts and serialised here rather than written into the
templates by hand, so every value is escaped correctly (a quote or a newline
in a title used to be able to break the JSON) and the same entities -- the
organisation, the website -- are described the same way on every page.
"""

import json

from django.conf import settings
from django.utils.safestring import mark_safe

from . import services

# Root-level files: (path inside static/, content type). Their URLs never
# change -- Google wants a stable favicon URL, which the hashed /static/ names
# are not.
BRAND_FILES = {
    "favicon.ico": ("website/brand/favicon.ico", "image/x-icon"),
    "favicon-48x48.png": ("website/brand/favicon-48x48.png", "image/png"),
    "favicon-96x96.png": ("website/brand/favicon-96x96.png", "image/png"),
    "apple-touch-icon.png": ("website/brand/apple-touch-icon.png", "image/png"),
    "icon-192.png": ("website/brand/icon-192.png", "image/png"),
    "icon-512.png": ("website/brand/icon-512.png", "image/png"),
    "og-image.png": ("website/brand/og-image.png", "image/png"),
}
LOGO_PATH = "/icon-512.png"
OG_IMAGE_PATH = "/og-image.png"


def script(data):
    """A JSON-LD <script> block. `</` is escaped so no value can close the tag."""
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return mark_safe(f'<script type="application/ld+json">{body}</script>')


def _id(name):
    return services.absolute(f"/#{name}")


def organization(site):
    org = {
        "@type": "Organization",
        "@id": _id("organization"),
        "name": site.site_name,
        "alternateName": "Pharmenta",
        "url": services.absolute("/"),
        "logo": {
            "@type": "ImageObject",
            "@id": _id("logo"),
            "url": services.absolute(LOGO_PATH),
            "width": 512,
            "height": 512,
            "caption": site.site_name,
        },
        "image": {"@id": _id("logo")},
    }
    if site.contact_email:
        org["email"] = site.contact_email
    same_as = [url for _key, _label, url in site.socials]
    if same_as:
        org["sameAs"] = same_as
    return org


def website(site):
    return {
        "@type": "WebSite",
        "@id": _id("website"),
        "name": site.site_name,
        "alternateName": ["Pharmenta", "فارمنتا Pharmenta"],
        "url": services.absolute("/"),
        "inLanguage": "fa-IR",
        "description": site.description,
        "publisher": {"@id": _id("organization")},
    }


def editorial_team():
    return {"@type": "Organization", "name": settings.SITE_EDITORIAL_NAME, "parentOrganization": {"@id": _id("organization")}}


def home_graph(site, *, title, description):
    """The homepage: who we are (Organization, with the logo Google may show)
    and what the site is called (WebSite, which Google reads for the site
    name next to results)."""
    return script({
        "@context": "https://schema.org",
        "@graph": [
            organization(site),
            website(site),
            {
                "@type": "WebPage",
                "@id": services.absolute("/"),
                "url": services.absolute("/"),
                "name": title,
                "description": description,
                "inLanguage": "fa-IR",
                "isPartOf": {"@id": _id("website")},
                "about": {"@id": _id("organization")},
                "primaryImageOfPage": {"@type": "ImageObject", "url": services.absolute(OG_IMAGE_PATH)},
            },
        ],
    })


def breadcrumbs(items):
    """BreadcrumbList for the trail a page shows: [(name, path or None)]; the
    last item is the page itself."""
    elements = []
    for position, (name, path) in enumerate(items, start=1):
        element = {"@type": "ListItem", "position": position, "name": name}
        if path:
            element["item"] = services.absolute(path)
        elements.append(element)
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def page_graph(site, *nodes):
    """An inner page's structured data, with the organisation and website its
    nodes point to (publisher, isPartOf) described on the same page."""
    return script({"@context": "https://schema.org", "@graph": [organization(site), website(site), *nodes]})


def article(post, site, *, canonical, image):
    author_name = post.author.get_full_name() if post.author_id else ""
    author = (
        {"@type": "Person", "name": author_name}
        if author_name
        else editorial_team()
    )
    node = {
        "@type": "BlogPosting",
        "headline": post.title[:110],
        "description": post.meta_description,
        "datePublished": post.published_at.isoformat() if post.published_at else None,
        "dateModified": post.updated_at.isoformat(),
        "inLanguage": "fa-IR",
        "mainEntityOfPage": canonical,
        "author": author,
        "publisher": {"@id": _id("organization")},
        "image": image or services.absolute(OG_IMAGE_PATH),
    }
    if post.category_id:
        node["articleSection"] = post.category.name
    tags = [t.name for t in post.tags.all()]
    if tags:
        node["keywords"] = tags
    return {k: v for k, v in node.items() if v is not None}
