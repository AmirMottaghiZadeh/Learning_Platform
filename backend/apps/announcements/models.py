"""Messages from the admin to the app's users: news, an update, a warning
or an offer, with an optional button to a web page or a part of the app.
They show as a card on the app's home (frontend components/announcements);
one a learner hasn't seen yet first shows with the screen behind it dimmed.

Each learner's receipt says whether they saw it, pressed its button or
closed it -- closing hides it for good -- and makes the admin's figures.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AppAnnouncement(models.Model):
    KIND_NEWS, KIND_UPDATE, KIND_WARNING, KIND_OFFER = "news", "update", "warning", "offer"
    KIND_CHOICES = [(KIND_NEWS, "خبر"), (KIND_UPDATE, "به‌روزرسانی"), (KIND_WARNING, "هشدار"), (KIND_OFFER, "پیشنهاد")]

    AUDIENCE_ALL, AUDIENCE_FREE, AUDIENCE_SUBSCRIBERS, AUDIENCE_OLD_APP = "all", "free", "subscribers", "old_app"
    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, "همهٔ کاربران"),
        (AUDIENCE_FREE, "فقط کاربران رایگان"),
        (AUDIENCE_SUBSCRIBERS, "فقط مشترک‌ها"),
        (AUDIENCE_OLD_APP, "نسخهٔ اپ قدیمی‌تر از…"),
    ]

    LINK_NONE, LINK_URL, LINK_APP = "", "url", "app"
    LINK_CHOICES = [(LINK_NONE, "بدون دکمه"), (LINK_URL, "نشانی وب"), (LINK_APP, "بخشی از اپ")]
    # Where an in-app button can go (frontend components/announcements/links.ts).
    SCREEN_CHOICES = [
        ("lessons", "درسنامه"),
        ("lesson", "یک گروه درسنامه (کد ATC)"),
        ("flashcards", "فلش‌کارت"),
        ("leitner", "جعبهٔ لایتنر"),
        ("quiz", "آزمون"),
        ("uptodate", "UpToDate"),
        ("lexicomp", "LexiComp"),
        ("calculator", "ماشین‌حساب‌ها"),
        ("guidelines", "راهنماهای بالینی"),
        ("diseases", "بیماری‌ها و شرایط"),
        ("planning", "برنامهٔ مطالعه"),
        ("statistics", "آمار"),
        ("downloads", "دانلود آفلاین"),
        ("profile", "پروفایل"),
    ]

    title = models.CharField(max_length=60)
    body = models.TextField(max_length=180)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_NEWS)
    cta_label = models.CharField(max_length=30, blank=True)
    link_kind = models.CharField(max_length=5, choices=LINK_CHOICES, blank=True, default=LINK_NONE)
    link_url = models.URLField(max_length=300, blank=True)
    link_screen = models.CharField(max_length=20, choices=SCREEN_CHOICES, blank=True)
    link_param = models.CharField(max_length=40, blank=True)
    audience = models.CharField(max_length=12, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    # For AUDIENCE_OLD_APP: shown to apps below this version ("0.2.0").
    below_version = models.CharField(max_length=20, blank=True)
    # None: from the moment it is published, and until it is ended.
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    dismissible = models.BooleanField(default=True)
    # A draft shows to this one account too: "test on my phone".
    test_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at", "-id"]

    def __str__(self):
        return self.title

    STATE_DRAFT, STATE_SCHEDULED, STATE_ACTIVE, STATE_ENDED = "draft", "scheduled", "active", "ended"
    STATE_LABELS = {STATE_DRAFT: "پیش‌نویس", STATE_SCHEDULED: "زمان‌بندی‌شده", STATE_ACTIVE: "فعال", STATE_ENDED: "پایان‌یافته"}

    def state_at(self, when=None):
        when = when or timezone.now()
        if not self.is_published:
            return self.STATE_DRAFT
        if self.ends_at and self.ends_at <= when:
            return self.STATE_ENDED
        if self.starts_at and self.starts_at > when:
            return self.STATE_SCHEDULED
        return self.STATE_ACTIVE

    @property
    def state(self):
        return self.state_at()

    @property
    def state_label(self):
        return self.STATE_LABELS[self.state]

    @property
    def has_button(self):
        return bool(self.cta_label) and self.link_kind in (self.LINK_URL, self.LINK_APP)


class AnnouncementReceipt(models.Model):
    """One learner and one announcement: when they saw it, pressed its button
    or closed it."""

    announcement = models.ForeignKey(AppAnnouncement, on_delete=models.CASCADE, related_name="receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    seen_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["announcement", "user"], name="announcement_receipt_once")]
