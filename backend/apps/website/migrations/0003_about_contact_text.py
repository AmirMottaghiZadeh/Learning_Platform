"""Replaces the first placeholder texts of the about and contact pages. A page
an editor has already rewritten in the panel is left alone."""

from django.db import migrations

from apps.website import page_texts

OLD_ABOUT = "<p>فارمنتا یک اپ آموزشی دوزبانهٔ داروشناسی است. درس‌ها بر پایهٔ طبقه‌بندی جهانی ATC و خلاصه‌ای از برچسب رسمی داروها ساخته شده‌اند و با فلش‌کارت و آزمون تکمیل می‌شوند.</p><h2>هدف ما</h2><p>یادگیری داروها را ساختاریافته و ماندگار کنیم؛ طوری که هر دارو را در جای درست طبقه‌بندی و کنار داروهای هم‌گروهش ببینید.</p><div class=\"callout\"><p>فارمنتا ابزار آموزشی است و جایگزین مرجع بالینی نیست.</p></div>"
OLD_CONTACT = "<p>پرسش، پیشنهاد یا گزارش مشکل دارید؟ پیام بگذارید.</p>"


def forwards(apps, schema_editor):
    Page = apps.get_model("website", "Page")
    for slug, old, new in (("about", OLD_ABOUT, page_texts.ABOUT), ("contact", OLD_CONTACT, page_texts.CONTACT)):
        page = Page.objects.filter(slug=slug).first()
        if page is not None and page.body_html.strip() in ("", old):
            page.body_html = new
            page.save(update_fields=["body_html", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0002_visitor_day"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
