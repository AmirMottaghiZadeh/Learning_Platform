"""Pages that go live are announced to IndexNow (see indexnow.py)."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from . import indexnow, services
from .models import Announcement, Page, Post


@receiver(post_save, sender=Post)
def post_saved(sender, instance, **kwargs):
    own = not instance.canonical_url or instance.canonical_url.rstrip("/") == services.absolute(instance.get_absolute_url()).rstrip("/")
    if instance.is_live and not instance.noindex and own:
        indexnow.notify([instance.get_absolute_url(), "/blog/"])


@receiver(post_save, sender=Page)
def page_saved(sender, instance, **kwargs):
    if instance.status == Page.PUBLISHED and not instance.noindex:
        indexnow.notify([instance.get_absolute_url()])


@receiver(post_save, sender=Announcement)
def announcement_saved(sender, instance, **kwargs):
    if instance.is_live:
        indexnow.notify([instance.get_absolute_url(), "/announcements/"])
