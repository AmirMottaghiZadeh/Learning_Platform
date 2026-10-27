"""The public pages: home, blog, plans, downloads, announcements, contact, pages,
and the machine-readable ones (sitemap, feed, robots)."""

import json
from datetime import timedelta
from xml.sax.saxutils import escape

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotModified
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_safe

from . import seo, services
from .models import (
    Announcement, AppRelease, Category, Comment, ContactMessage, ContentBlock, DailyStat, DownloadLink, Media, Page, Post,
    SiteSettings, Subscriber, Tag,
)
from .sanitize import plain_text


def _page_meta(request, *, title="", description="", image=None, noindex=False, canonical=None, kind="website"):
    site = SiteSettings.get()
    suffix = f" {site.title_suffix}" if site.title_suffix and title else ""
    og = image or (site.default_og_image.url if site.default_og_image_id else "")
    path = canonical if canonical is not None else request.path
    return {
        "meta_title": (title + suffix) if title else f"{site.site_name} | {site.tagline}",
        "meta_description": description or site.description,
        "meta_image": services.absolute(og) if og and og.startswith("/") else og,
        "meta_noindex": noindex or site.noindex_site,
        "meta_canonical": path if path.startswith("http") else services.absolute(path),
        "meta_type": kind,
    }


def home(request):
    site = SiteSettings.get()
    services.record_view(request, "/")
    ctx = {
        "blocks": services.blocks(),
        "cards": services.plan_cards(),
        "posts": list(services.live_posts().order_by("-featured", "-published_at")[:3]),
        "announcement": services.latest_announcement(),
        "downloads": list(DownloadLink.objects.filter(is_active=True)),
        "nav": "home",
    }
    if settings.SITE_DRUG_ATC_PREFIXES:
        from .views_drugs import popular

        ctx["drugs"] = popular()
    ctx.update(_page_meta(request, description=site.description, canonical="/"))
    ctx["structured_data"] = seo.home_graph(site, title=ctx["meta_title"], description=" ".join(site.description.split()))
    return render(request, "website/home.html", ctx)


def blog_index(request):
    site = SiteSettings.get()
    query = (request.GET.get("q") or "").strip()
    qs = services.search_posts(query) if query else services.live_posts()
    page = Paginator(qs, site.posts_per_page or 9).get_page(request.GET.get("page"))
    services.record_view(request, "/blog/")
    ctx = {
        "page": page, "query": query, "categories": Category.objects.all(), "nav": "blog",
        "featured": None if query or page.number > 1 else services.live_posts().filter(featured=True).first(),
    }
    ctx.update(_page_meta(request, title="مقالات" if not query else f"جست‌وجوی «{query}»",
                          description="مقاله‌های آموزش داروشناسی، طبقه‌بندی ATC و روش‌های یادگیری.",
                          noindex=bool(query) or page.number > 1, canonical="/blog/"))
    return render(request, "website/blog_list.html", ctx)


def category(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    page = Paginator(services.live_posts().filter(category=cat), SiteSettings.get().posts_per_page or 9).get_page(request.GET.get("page"))
    services.record_view(request, request.path)
    ctx = {"page": page, "heading": cat.name, "subheading": cat.description, "categories": Category.objects.all(), "active_category": cat, "nav": "blog"}
    ctx.update(_page_meta(request, title=cat.seo_title or cat.name, description=cat.seo_description or cat.description))
    return render(request, "website/blog_list.html", ctx)


def tag(request, slug):
    t = get_object_or_404(Tag, slug=slug)
    page = Paginator(services.live_posts().filter(tags=t), SiteSettings.get().posts_per_page or 9).get_page(request.GET.get("page"))
    services.record_view(request, request.path)
    ctx = {"page": page, "heading": f"برچسب: {t.name}", "categories": Category.objects.all(), "nav": "blog"}
    ctx.update(_page_meta(request, title=f"برچسب {t.name}", noindex=page.number > 1))
    return render(request, "website/blog_list.html", ctx)


def post_detail(request, slug):
    qs = Post.objects.select_related("category", "cover", "author").prefetch_related("tags")
    post = get_object_or_404(qs, slug=slug)
    if not post.is_live:
        from .permissions import can

        if not (can(request.user, "post.view_all") or services.preview_ok(request, post)):
            raise Http404
        messages.info(request, "این مطلب هنوز منتشر نشده و فقط شما آن را می‌بینید.")
    body, toc = services.add_toc(post.body_html)
    site = SiteSettings.get()
    related = services.live_posts().exclude(pk=post.pk)
    related = (related.filter(category=post.category) if post.category_id else related)[:3]
    siblings = services.live_posts().exclude(pk=post.pk)
    older = siblings.filter(published_at__lt=post.published_at).order_by("-published_at").first() if post.published_at else None
    newer = siblings.filter(published_at__gt=post.published_at).order_by("published_at").first() if post.published_at else None
    comments = []
    if site.comments_enabled and post.allow_comments:
        top = post.comments.filter(status=Comment.APPROVED, parent__isnull=True).prefetch_related("replies")
        comments = [(c, [r for r in c.replies.all() if r.status == Comment.APPROVED]) for c in top]
    if post.is_live:
        services.record_view(request, request.path, post=post)
    image = post.cover.url if post.cover_id else None
    ctx = {
        "post": post, "body": body, "toc": toc, "related": related, "older": older, "newer": newer,
        "comments": comments, "comment_count": sum(1 + len(r) for _, r in comments), "nav": "blog",
        "comments_open": site.comments_enabled and post.allow_comments,
    }
    ctx.update(_page_meta(request, title=post.meta_title, description=post.meta_description, image=image,
                          noindex=post.noindex or not post.is_live, canonical=post.canonical_url or post.get_absolute_url(), kind="article"))
    if post.is_live:
        trail = [("خانه", "/"), ("مقالات", "/blog/")]
        if post.category_id:
            trail.append((post.category.name, post.category.get_absolute_url()))
        trail.append((post.title, None))
        ctx["structured_data"] = seo.page_graph(
            site, seo.breadcrumbs(trail), seo.article(post, site, canonical=ctx["meta_canonical"], image=ctx["meta_image"] or None),
        )
    return render(request, "website/post_detail.html", ctx)


@require_POST
def comment_post(request, slug):
    post = get_object_or_404(Post.objects.live(), slug=slug)
    site = SiteSettings.get()
    back = redirect(f"{post.get_absolute_url()}#comments")
    if not (site.comments_enabled and post.allow_comments):
        return back
    if request.POST.get("website"):  # honeypot
        return back
    if not services.throttle(request, "comment", 4, 600):
        messages.error(request, "تعداد نظرهای شما در این بازه زیاد بود؛ کمی بعد دوباره تلاش کنید.")
        return back
    name = (request.POST.get("name") or "").strip()[:80]
    body = (request.POST.get("body") or "").strip()[:2000]
    email = (request.POST.get("email") or "").strip()
    if not name or len(body) < 3:
        messages.error(request, "نام و متن نظر را بنویسید.")
        return back
    try:
        if email:
            validate_email(email)
    except ValidationError:
        messages.error(request, "ایمیل معتبر نیست.")
        return back
    parent = None
    if request.POST.get("parent"):
        parent = Comment.objects.filter(pk=request.POST["parent"], post=post, parent__isnull=True, status=Comment.APPROVED).first()
    status = Comment.PENDING if site.comments_moderated else Comment.APPROVED
    Comment.objects.create(post=post, parent=parent, name=name, email=email, body=body, status=status, ip_hash=services.ip_hash(request))
    messages.success(request, "نظر شما ثبت شد و پس از تأیید نمایش داده می‌شود." if status == Comment.PENDING else "نظر شما ثبت شد.")
    return back


def plans(request):
    services.record_view(request, "/plans/")
    cards = services.plan_cards(products=True)
    ctx = {"cards": cards, "compare": services.compare_rows(cards), "blocks": services.blocks(), "nav": "plans"}
    ctx.update(_page_meta(request, title="پلن‌ها و خرید اشتراک", description="پلن‌های اشتراک فارمنتا و امکانات هر کدام."))
    return render(request, "website/plans.html", ctx)


def download(request):
    services.record_view(request, "/download/")
    releases = AppRelease.objects.filter(is_published=True)
    latest = {r.platform: r for r in releases.filter(is_latest=True, channel=AppRelease.STABLE)}
    ctx = {
        "links": DownloadLink.objects.filter(is_active=True), "latest": latest, "releases": releases[:12], "nav": "download",
    }
    ctx.update(_page_meta(request, title="دانلود اپ", description="دانلود فارمنتا برای اندروید و iOS یا استفاده از نسخهٔ وب."))
    return render(request, "website/download.html", ctx)


def download_click(request, pk):
    link = get_object_or_404(DownloadLink, pk=pk, is_active=True)
    if not services.is_bot(request):
        DownloadLink.objects.filter(pk=link.pk).update(clicks=link.clicks + 1)
        DailyStat.bump(DailyStat.DOWNLOAD, link.store)
    return redirect(link.url)


def announcements(request):
    qs = Announcement.objects.filter(is_published=True, published_at__lte=timezone.now())
    page = Paginator(qs, 10).get_page(request.GET.get("page"))
    services.record_view(request, "/announcements/")
    ctx = {"page": page, "nav": "announcements"}
    ctx.update(_page_meta(request, title="اطلاعیه‌ها", description="تازه‌ترین اطلاعیه‌ها و نسخه‌های فارمنتا."))
    return render(request, "website/announcements.html", ctx)


def announcement_detail(request, slug):
    item = get_object_or_404(Announcement, slug=slug)
    if not item.is_live:
        raise Http404
    services.record_view(request, request.path)
    ctx = {"item": item, "nav": "announcements"}
    ctx.update(_page_meta(request, title=item.title, description=item.summary))
    return render(request, "website/announcement_detail.html", ctx)


def contact(request):
    page = Page.objects.filter(kind=Page.KIND_CONTACT, status=Page.PUBLISHED).first()
    if request.method == "POST":
        if request.POST.get("website"):
            return redirect(request.path)
        if not services.throttle(request, "contact", 3, 900):
            messages.error(request, "پیام‌های پشت‌سرهم ثبت نمی‌شود؛ کمی بعد دوباره تلاش کنید.")
            return redirect(request.path)
        name = (request.POST.get("name") or "").strip()[:100]
        text = (request.POST.get("message") or "").strip()[:4000]
        email = (request.POST.get("email") or "").strip()[:254]
        errors = []
        if not name:
            errors.append("نام را بنویسید.")
        if len(text) < 5:
            errors.append("پیام را بنویسید.")
        try:
            if email:
                validate_email(email)
        except ValidationError:
            errors.append("ایمیل معتبر نیست.")
        if not email and not (request.POST.get("phone") or "").strip():
            errors.append("ایمیل یا شمارهٔ تماس را بنویسید تا بتوانیم پاسخ دهیم.")
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "website/contact.html", {"page": page, "form": request.POST, "nav": "contact", **_page_meta(request, title="تماس با ما")})
        ContactMessage.objects.create(
            name=name, email=email, phone=(request.POST.get("phone") or "").strip()[:20],
            subject=(request.POST.get("subject") or "").strip()[:160], message=text, ip_hash=services.ip_hash(request),
        )
        DailyStat.bump(DailyStat.CONTACT)
        messages.success(request, "پیام شما ثبت شد. در اولین فرصت پاسخ می‌دهیم.")
        return redirect(request.path)
    services.record_view(request, request.path)
    ctx = {"page": page, "form": {}, "nav": "contact"}
    ctx.update(_page_meta(request, title=(page.meta_title if page else "تماس با ما"), description=(page.meta_description if page else "")))
    return render(request, "website/contact.html", ctx)


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    if page.kind == Page.KIND_CONTACT:
        return contact(request)
    if page.status != Page.PUBLISHED:
        from .permissions import can

        if not can(request.user, "page.manage"):
            raise Http404
    services.record_view(request, request.path)
    ctx = {"page": page, "nav": f"page:{page.slug}"}
    ctx.update(_page_meta(request, title=page.meta_title, description=page.meta_description, noindex=page.noindex or page.status != Page.PUBLISHED))
    if page.status == Page.PUBLISHED and not page.noindex:
        ctx["structured_data"] = seo.page_graph(SiteSettings.get(), seo.breadcrumbs([("خانه", "/"), (page.title, None)]))
    return render(request, "website/page.html", ctx)


@require_POST
def subscribe(request):
    site = SiteSettings.get()
    back = request.META.get("HTTP_REFERER") or "/"
    if not request.POST.get("website") and site.newsletter_enabled and services.throttle(request, "subscribe", 5, 600):
        email = (request.POST.get("email") or "").strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "ایمیل معتبر نیست.")
            return redirect(back)
        sub, created = Subscriber.objects.get_or_create(email=email, defaults={"source": (request.POST.get("source") or "")[:40]})
        if not created and not sub.is_active:
            sub.is_active = True
            sub.save(update_fields=["is_active"])
        if created:
            DailyStat.bump(DailyStat.SUBSCRIBE)
        messages.success(request, "عضویت شما در خبرنامه ثبت شد.")
    return redirect(back)


def search(request):
    return redirect(f"{reverse('site:blog')}?q={request.GET.get('q', '')}")


# -- machine readable -------------------------------------------------------------

@require_GET
def media(request, pk, name):
    item = get_object_or_404(Media, pk=pk)
    etag = f'"{item.sha256[:32]}"'
    if request.META.get("HTTP_IF_NONE_MATCH") == etag:
        return HttpResponseNotModified()
    response = HttpResponse(bytes(item.data), content_type=item.content_type)
    response["ETag"] = etag
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = f'inline; filename="{item.filename}"'
    response["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
    return response


@require_safe
def brand_file(request, name):
    """An icon at a fixed root URL (/favicon.ico, /apple-touch-icon.png, ...),
    served from the app's static files so its address never changes."""
    path, content_type = seo.BRAND_FILES[name]
    found = finders.find(path)
    if not found:
        raise Http404
    response = FileResponse(open(found, "rb"), content_type=content_type)
    response["Cache-Control"] = "public, max-age=604800"
    return response


@require_GET
def webmanifest(request):
    site = SiteSettings.get()
    body = {
        "name": site.site_name,
        "short_name": site.site_name,
        "description": " ".join(site.description.split()),
        "lang": "fa",
        "dir": "rtl",
        "start_url": "/",
        "display": "browser",
        "background_color": "#EDF5F0",
        "theme_color": "#EDF5F0",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    response = HttpResponse(json.dumps(body, ensure_ascii=False), content_type="application/manifest+json; charset=utf-8")
    response["Cache-Control"] = "public, max-age=86400"
    return response


@require_GET
def robots(request):
    site = SiteSettings.get()
    if site.noindex_site:
        body = "User-agent: *\nDisallow: /\n"
    else:
        body = "User-agent: *\nAllow: /\nDisallow: /panel/\nDisallow: /ops/\nDisallow: /account/\nDisallow: /checkout/\nDisallow: /pay/\nDisallow: /dl/\n"
        if site.robots_extra.strip():
            body += site.robots_extra.strip() + "\n"
        body += f"\nSitemap: {services.absolute('/sitemap.xml')}\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_safe
def verification_file(request):
    """An empty file at the site root that eNamad fetches to confirm we own
    the domain. HEAD is allowed too, in case the checker only asks for that."""
    return HttpResponse("", content_type="text/plain; charset=utf-8")


@require_GET
def sitemap(request):
    entries = [("/", None, "1.0"), ("/blog/", None, "0.8"), ("/plans/", None, "0.8"), ("/download/", None, "0.7"), ("/announcements/", None, "0.5")]
    if settings.SITE_DRUG_ATC_PREFIXES:
        from .views_drugs import catalog

        drugs = catalog()
        if drugs:
            entries.append(("/drugs/", max(d["updated"] for d in drugs), "0.9"))
            entries += [(f"/drugs/{d['slug']}/", d["updated"], "0.8") for d in drugs]
    posts = Post.objects.live().filter(noindex=False).only("slug", "updated_at", "canonical_url")
    entries += [(p.get_absolute_url(), p.updated_at, "0.7") for p in posts if not p.canonical_url or p.canonical_url.rstrip("/") == services.absolute(p.get_absolute_url()).rstrip("/")]
    entries += [(p.get_absolute_url(), p.updated_at, "0.4") for p in Page.objects.filter(status=Page.PUBLISHED, noindex=False).exclude(kind=Page.KIND_CONTACT).only("slug", "updated_at")]
    entries += [("/contact/", None, "0.3")]
    entries += [(c.get_absolute_url(), None, "0.5") for c in Category.objects.filter(posts__in=Post.objects.live()).distinct()]
    entries += [(a.get_absolute_url(), None, "0.4") for a in Announcement.objects.filter(is_published=True, published_at__lte=timezone.now())]
    rows = []
    for path, modified, priority in entries:
        lastmod = f"<lastmod>{modified.date().isoformat()}</lastmod>" if modified else ""
        rows.append(f"<url><loc>{escape(services.absolute(path))}</loc>{lastmod}<priority>{priority}</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(rows) + "</urlset>"
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


@require_GET
def feed(request):
    site = SiteSettings.get()
    items = []
    for post in services.live_posts()[:20]:
        link = services.absolute(post.get_absolute_url())
        items.append(
            f"<item><title>{escape(post.title)}</title><link>{escape(link)}</link><guid>{escape(link)}</guid>"
            f"<pubDate>{post.published_at.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
            f"<description>{escape(post.meta_description)}</description></item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{escape(site.site_name)}</title><link>{escape(services.absolute('/'))}</link>"
        f"<description>{escape(site.description)}</description><language>fa</language>{''.join(items)}</channel></rss>"
    )
    return HttpResponse(xml, content_type="application/rss+xml; charset=utf-8")


def not_found(request, exception=None):
    return render(request, "website/404.html", {"nav": ""}, status=404)
