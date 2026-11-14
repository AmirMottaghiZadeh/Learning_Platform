"""Add the cornerstone articles and the editorial-policy page as drafts, and
the drug pages to the site's menus. Idempotent: an article or page whose
slug exists is left alone, as is a menu that already links to /drugs/, so
nothing an editor has changed is overwritten.

    python manage.py seed_seo_content
    python manage.py seed_seo_content --dry-run
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse

from apps.website import seo_articles
from apps.website.models import SITE_URLCONF, Category, MenuItem, Page, Post, Tag, unique_slug
from apps.website.sanitize import clean_html
from apps.website.views_drugs import catalog

MENU_LINKS = [
    (MenuItem.HEADER, "دارونامه", 15),
    (MenuItem.FOOT_RESOURCES, "دارونامه", 5),
]
PLACEHOLDER = re.compile(r"\[\[(drugs|drug:([a-z0-9 \-]+))\]\]")


def render_links(body, by_name):
    drugs_url = reverse("site:drugs", urlconf=SITE_URLCONF)

    def link(match):
        if match.group(1) == "drugs":
            return f'<a href="{drugs_url}">دارونامهٔ فارمنتا</a>'
        entry = by_name.get(match.group(2))
        if entry is None:
            return match.group(2)
        return f'<a href="{reverse("site:drug", args=[entry["slug"]], urlconf=SITE_URLCONF)}">{entry["name_fa"]}</a>'

    return PLACEHOLDER.sub(link, body)


class Command(BaseCommand):
    help = "Add the cornerstone SEO articles and editorial page as drafts, and the drug pages to the menus."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report what would be added, then roll back.")

    def handle(self, *args, dry_run=False, **options):
        by_name = {e["name"].lower(): e for e in catalog()}
        unresolved = set()
        for article in seo_articles.ARTICLES:
            for match in PLACEHOLDER.finditer(article["body"]):
                if match.group(2) and match.group(2) not in by_name:
                    unresolved.add(match.group(2))

        with transaction.atomic():
            made = self._seed(by_name)
            if dry_run:
                transaction.set_rollback(True)

        for line in made or ["nothing to add"]:
            self.stdout.write(line)
        if unresolved:
            self.stdout.write(self.style.WARNING(
                "No drug page for: " + ", ".join(sorted(unresolved)) + " -- written as plain names."
            ))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: nothing was saved."))

    def _seed(self, by_name):
        made = []
        spec = seo_articles.CATEGORY
        category, created = Category.objects.get_or_create(
            slug=spec["slug"],
            defaults={k: spec[k] for k in ("name", "description", "seo_title", "seo_description")},
        )
        if created:
            made.append(f"category: {category.name}")

        for spec in seo_articles.ARTICLES:
            if Post.objects.filter(slug=spec["slug"]).exists():
                continue
            post = Post.objects.create(
                title=spec["title"], slug=spec["slug"], excerpt=spec["excerpt"],
                body_html=clean_html(render_links(spec["body"], by_name).strip()),
                category=category, status=Post.DRAFT,
                seo_title=spec["seo_title"], seo_description=spec["seo_description"],
            )
            for name in spec["tags"]:
                tag = Tag.objects.filter(name=name).first() or Tag.objects.create(name=name, slug=unique_slug(Tag, name))
                post.tags.add(tag)
            made.append(f"draft post: {post.title}")

        spec = seo_articles.EDITORIAL_PAGE
        if not Page.objects.filter(slug=spec["slug"]).exists():
            Page.objects.create(
                title=spec["title"], slug=spec["slug"], body_html=clean_html(spec["body"].strip()), status=Page.DRAFT,
                seo_title=spec["seo_title"], seo_description=spec["seo_description"],
            )
            made.append(f"draft page: {spec['title']}")

        drugs_url = reverse("site:drugs", urlconf=SITE_URLCONF)
        if catalog():
            for location, label, order in MENU_LINKS:
                if not MenuItem.objects.filter(location=location, url=drugs_url).exists():
                    MenuItem.objects.create(location=location, label=label, url=drugs_url, order=order)
                    made.append(f"menu ({location}): {label}")
        return made
