"""Read-side logic for the public pages, and small helpers shared with the panel."""

import hashlib
import re
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.text import slugify

from .models import Announcement, ContentBlock, DailyStat, Post

BOT_RE = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|preview|monitor|uptime|curl|wget|python-requests", re.I)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")) or "0.0.0.0"


def ip_hash(request):
    return hashlib.sha256(f"{settings.SECRET_KEY}:{client_ip(request)}".encode()).hexdigest()


def is_bot(request):
    return bool(BOT_RE.search(request.META.get("HTTP_USER_AGENT", ""))) or request.method == "HEAD"


def throttle(request, scope, limit, seconds):
    """True while the caller is under `limit` hits per `seconds` for `scope`."""
    key = f"website:throttle:{scope}:{ip_hash(request)[:24]}"
    if cache.add(key, 1, seconds):
        return True
    try:
        return cache.incr(key) <= limit
    except ValueError:
        cache.set(key, 1, seconds)
        return True


def record_view(request, key, *, post=None):
    """Counts a page view unless it is a bot, staff, or the panel."""
    if is_bot(request) or (request.user.is_authenticated and request.user.is_staff):
        return
    DailyStat.bump(DailyStat.VIEW, key[:200])
    if post is not None:
        DailyStat.bump(DailyStat.POST, str(post.pk))
        Post.objects.filter(pk=post.pk).update(views=post.views + 1)


# -- content blocks ------------------------------------------------------------

def blocks():
    """The home page blocks grouped by kind."""
    grouped = {kind: [] for kind, _ in ContentBlock.KINDS}
    for block in ContentBlock.objects.filter(is_active=True):
        grouped[block.kind].append(block)
    return grouped


# -- plans ---------------------------------------------------------------------

def plan_cards(*, products=False):
    """What is for sale, shaped for the pricing sections: one card per plan
    with its features and priced durations."""
    from apps.billing.models import Plan, PlanFeature

    kinds = [Plan.KIND_PLAN] + ([Plan.KIND_PRODUCT] if products else [])
    plans = (
        Plan.objects.filter(kind__in=kinds, status=Plan.STATUS_ACTIVE)
        .prefetch_related(
            "prices",
            Prefetch("plan_features", queryset=PlanFeature.objects.select_related("feature").order_by("feature__order")),
        )
        .order_by("kind", "order", "id")
    )
    cards = []
    for plan in plans:
        prices = [p for p in plan.prices.all() if p.is_active]
        features = []
        for pf in plan.plan_features.all():
            if not pf.feature.is_active:
                continue
            limit = pf.limit if pf.feature.countable and pf.limit is not None else None
            period = pf.get_period_display() if limit is not None else ""
            features.append({"name": pf.feature.name_fa, "limit": limit, "period": period, "unit": pf.feature.unit_fa})
        cards.append({"plan": plan, "prices": prices, "features": features})
    return cards


# -- posts ---------------------------------------------------------------------

def live_posts():
    return Post.objects.live().select_related("category", "cover", "author").prefetch_related("tags")


def search_posts(query):
    query = (query or "").strip()
    if len(query) < 2:
        return Post.objects.none()
    q = Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(body_html__icontains=query)
    return live_posts().filter(q)


_HEADING = re.compile(r"<(h[23])>(.*?)</\1>", re.S)


def add_toc(body_html):
    """(html with ids on h2/h3, [(id, level, text)])."""
    toc, used = [], set()

    def repl(match):
        tag, inner = match.group(1), match.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        base = slugify(text, allow_unicode=True) or "section"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        toc.append((slug, int(tag[1]), text))
        return f'<{tag} id="{slug}">{inner}</{tag}>'

    return _HEADING.sub(repl, body_html or ""), toc


def latest_announcement():
    return (
        Announcement.objects.filter(is_published=True, published_at__lte=timezone.now(),
                                    published_at__gte=timezone.now() - timedelta(days=45))
        .order_by("-pinned", "-published_at").first()
    )


def absolute(path):
    return settings.SITE_PUBLIC_URL.rstrip("/") + path


def compare_rows(cards):
    """Rows for the plan comparison table: each feature, and per plan None
    (not included), "" (included) or the limit as text."""
    names = []
    for card in cards:
        for f in card["features"]:
            if f["name"] not in names:
                names.append(f["name"])
    rows = []
    for name in names:
        cells = []
        for card in cards:
            hit = next((f for f in card["features"] if f["name"] == name), None)
            if hit is None:
                cells.append(None)
            elif hit["limit"] is None:
                cells.append("")
            else:
                cells.append(f"{hit['limit']} {hit['unit']} {hit['period']}".strip())
        rows.append({"name": name, "cells": cells})
    return rows
