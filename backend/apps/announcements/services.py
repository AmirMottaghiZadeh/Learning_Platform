from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.billing.models import Entitlement
from apps.website.models import version_code

from .models import AnnouncementReceipt, AppAnnouncement


def _is_subscriber(user, now):
    return Entitlement.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now), user=user, revoked_at__isnull=True, starts_at__lte=now
    ).exists()


def _for_audience(item, *, subscriber, app_code):
    if item.audience == AppAnnouncement.AUDIENCE_FREE:
        return not subscriber
    if item.audience == AppAnnouncement.AUDIENCE_SUBSCRIBERS:
        return subscriber
    if item.audience == AppAnnouncement.AUDIENCE_OLD_APP:
        # an app that didn't say its version isn't shown a version notice
        return app_code is not None and bool(item.below_version) and app_code < version_code(item.below_version)
    return True


def for_user(user, app_code=None, when=None, *, pwa_state=None):
    """What `user`'s app shows now: published ones in their time window and
    audience, and drafts sent to them to test; none they closed. Pinned
    first, then the newest. Each comes with its receipt (or None)."""
    now = when or timezone.now()
    live = Q(is_published=True) & (Q(starts_at__isnull=True) | Q(starts_at__lte=now)) & (Q(ends_at__isnull=True) | Q(ends_at__gt=now))
    items = list(
        AppAnnouncement.objects.filter(live | Q(test_user=user))
        .annotate(shown_from=Coalesce("starts_at", "created_at"))
        .order_by("-is_pinned", "-shown_from", "-id")
    )
    if not items:
        return []
    receipts = {r.announcement_id: r for r in AnnouncementReceipt.objects.filter(user=user, announcement__in=items)}
    subscriber = _is_subscriber(user, now)
    out = []
    for item in items:
        # Older clients never receive a button action they cannot handle.
        # A test draft must respect this too: native/standalone cannot install.
        if (item.link_kind == AppAnnouncement.LINK_PWA or item.audience == AppAnnouncement.AUDIENCE_WEB_NEW) and pwa_state != "browser":
            continue
        receipt = receipts.get(item.pk)
        if receipt and receipt.dismissed_at and (item.dismissible or item.link_kind == AppAnnouncement.LINK_PWA):
            continue
        if item.test_user_id != user.pk and not _for_audience(item, subscriber=subscriber, app_code=app_code):
            continue
        out.append((item, receipt))
    return out


EVENTS = ("seen", "click", "dismiss")


def record(user, item, event):
    """Note what `user` did with `item`; the first time of each counts."""
    receipt, _ = AnnouncementReceipt.objects.get_or_create(announcement=item, user=user)
    now = timezone.now()
    fields = []
    if receipt.seen_at is None:
        receipt.seen_at = now
        fields.append("seen_at")
    if event == "click" and receipt.clicked_at is None:
        receipt.clicked_at = now
        fields.append("clicked_at")
    if event == "dismiss" and (item.dismissible or item.link_kind == AppAnnouncement.LINK_PWA) and receipt.dismissed_at is None:
        receipt.dismissed_at = now
        fields.append("dismissed_at")
    if fields:
        receipt.save(update_fields=fields)
    return receipt


def with_figures(qs):
    """Each announcement with how many saw it, pressed its button, closed it."""
    return qs.annotate(
        n_seen=Count("receipts", filter=Q(receipts__seen_at__isnull=False)),
        n_clicked=Count("receipts", filter=Q(receipts__clicked_at__isnull=False)),
        n_dismissed=Count("receipts", filter=Q(receipts__dismissed_at__isnull=False)),
    )
