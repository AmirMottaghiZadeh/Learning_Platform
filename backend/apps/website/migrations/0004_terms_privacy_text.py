"""Gives the terms and privacy pages their real text and publishes them. A page
still holding the seed's placeholder (or nothing) gets the text; a page an
editor has already written in the panel is left alone. A live site missing
one of the two pages gets it; an empty database is left to the seed command,
which makes all the standard pages at once."""

from django.db import migrations

from apps.website import page_texts

PAGES = (
    ("terms", "قوانین و مقررات", "<p>متن قوانین و مقررات را در پنل ویرایش کنید.</p>", page_texts.TERMS),
    ("privacy", "حریم خصوصی", "<p>متن حریم خصوصی را در پنل ویرایش کنید.</p>", page_texts.PRIVACY),
)


def forwards(apps, schema_editor):
    Page = apps.get_model("website", "Page")
    if not Page.objects.exists():
        return
    for slug, title, placeholder, text in PAGES:
        page = Page.objects.filter(slug=slug).first()
        if page is None:
            Page.objects.create(title=title, slug=slug, body_html=text.strip(), status="published")
        elif page.body_html.strip() in ("", placeholder):
            page.body_html = text.strip()
            page.status = "published"
            page.save(update_fields=["body_html", "status", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0003_about_contact_text"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
