from django import forms
from django.utils import timezone

from ..models import (
    Announcement, AppRelease, Category, ContentBlock, DownloadLink, Media, MenuItem, Page, Post, Redirect, SiteSettings, Tag,
    make_slug, unique_slug, version_code,
)
from ..sanitize import clean_html
from .ui import JalaliDateTimeField, PanelForm, RichTextWidget, StyledFormMixin


class SlugMixin:
    """Fills an empty slug from `slug_source` and keeps it unique."""

    slug_source = "title"

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        base = slug or self.data.get(self.slug_source, "")
        if not make_slug(base, fallback=""):
            raise forms.ValidationError("نشانی را بنویسید.")
        return unique_slug(self._meta.model, base, exclude_pk=self.instance.pk)


class PostForm(SlugMixin, PanelForm):
    tags_text = forms.CharField(label="برچسب‌ها", required=False, help_text="با ویرگول جدا کنید.",
                                widget=forms.TextInput(attrs={"placeholder": "ATC، لایتنر، دارو"}))
    published_at = JalaliDateTimeField(label="زمان انتشار", required=False,
                                       help_text="خالی = همین حالا. برای زمان‌بندی، وضعیت «زمان‌بندی‌شده» و تاریخ آینده را بدهید.")
    cover = forms.ModelChoiceField(queryset=Media.objects.all(), required=False, widget=forms.HiddenInput)

    class Meta:
        model = Post
        fields = ["title", "slug", "excerpt", "body_html", "cover", "category", "status", "published_at", "featured",
                  "allow_comments", "seo_title", "seo_description", "canonical_url", "noindex"]
        widgets = {"body_html": RichTextWidget(), "excerpt": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        self.allow_publish = kwargs.pop("allow_publish", True)
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["category"].required = False
        self.fields["category"].empty_label = "— بدون دسته —"
        if self.instance.pk:
            self.fields["tags_text"].initial = "، ".join(self.instance.tags.values_list("name", flat=True))
        if not self.allow_publish:
            self.fields["status"].choices = [(Post.DRAFT, "پیش‌نویس"), (Post.REVIEW, "ارسال برای بازبینی")]
            for f in ("featured", "published_at"):
                self.fields.pop(f)
        self._style()

    def clean_body_html(self):
        return clean_html(self.cleaned_data.get("body_html"))

    def clean(self):
        data = super().clean()
        status, when = data.get("status"), data.get("published_at")
        if status == Post.SCHEDULED:
            if not when or when <= timezone.now():
                self.add_error("published_at", "برای زمان‌بندی، تاریخ و ساعتی در آینده بنویسید.")
        elif status == Post.PUBLISHED and not when:
            data["published_at"] = self.instance.published_at or timezone.now()
        return data

    def save_tags(self, post):
        names = [n.strip() for n in self.cleaned_data.get("tags_text", "").replace("،", ",").split(",") if n.strip()]
        tags = []
        for name in dict.fromkeys(names):
            tag = Tag.objects.filter(name=name).first() or Tag.objects.create(name=name[:60], slug=unique_slug(Tag, name))
            tags.append(tag)
        post.tags.set(tags)


class CategoryForm(SlugMixin, PanelForm):
    slug_source = "name"

    class Meta:
        model = Category
        fields = ["name", "slug", "description", "order", "seo_title", "seo_description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False


class TagForm(SlugMixin, PanelForm):
    slug_source = "name"

    class Meta:
        model = Tag
        fields = ["name", "slug"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False


class PageForm(SlugMixin, PanelForm):
    class Meta:
        model = Page
        fields = ["title", "slug", "kind", "body_html", "status", "seo_title", "seo_description", "noindex"]
        widgets = {"body_html": RichTextWidget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def clean_body_html(self):
        return clean_html(self.cleaned_data.get("body_html"))


class AnnouncementForm(SlugMixin, PanelForm):
    published_at = JalaliDateTimeField(label="زمان انتشار", required=False)

    class Meta:
        model = Announcement
        fields = ["title", "slug", "level", "body_html", "is_published", "published_at", "pinned"]
        widgets = {"body_html": RichTextWidget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def clean_body_html(self):
        return clean_html(self.cleaned_data.get("body_html"))

    def clean_published_at(self):
        return self.cleaned_data.get("published_at") or timezone.now()


class ReleaseForm(PanelForm):
    released_at = JalaliDateTimeField(label="تاریخ انتشار", with_time=False, required=False)

    class Meta:
        model = AppRelease
        fields = ["platform", "version", "channel", "released_at", "size_mb", "min_os", "notes_html", "is_published", "is_latest",
                  "notify_in_app", "min_supported_version"]
        widgets = {"notes_html": RichTextWidget()}

    def clean_released_at(self):
        return self.cleaned_data.get("released_at") or timezone.localdate()

    def clean(self):
        data = super().clean()
        if not data.get("notify_in_app"):
            return data
        # The app compares versions as numbers (models.version_code).
        if data.get("platform") == AppRelease.WEB:
            self.add_error("notify_in_app", "وب‌اپ با هر دیپلوی خودش به‌روز می‌شود.")
        if data.get("channel") != AppRelease.STABLE or not data.get("is_published"):
            self.add_error("notify_in_app", "فقط نسخهٔ پایدار و منتشرشده را می‌شود در اپ اعلام کرد.")
        codes = {}
        for field in ("version", "min_supported_version"):
            value = (data.get(field) or "").strip()
            if not value:
                continue
            try:
                codes[field] = version_code(value)
            except ValueError:
                self.add_error(field, "به شکل 1.4.2 و با رقم‌های لاتین بنویسید (عدد دوم و سوم کمتر از ۱۰۰)، همان version در frontend/app.json.")
        if codes.get("min_supported_version", 0) > codes.get("version", 10**9):
            self.add_error("min_supported_version", "از خود این نسخه بالاتر است.")
        return data

    def clean_notes_html(self):
        return clean_html(self.cleaned_data.get("notes_html"))


class DownloadLinkForm(PanelForm):
    class Meta:
        model = DownloadLink
        fields = ["store", "label", "url", "platform", "order", "is_active"]


class MenuItemForm(PanelForm):
    class Meta:
        model = MenuItem
        fields = ["location", "label", "url", "order", "is_active", "new_tab"]


class ContentBlockForm(PanelForm):
    class Meta:
        model = ContentBlock
        fields = ["kind", "title", "text", "badge", "bullets", "screen", "order", "is_active"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3}), "bullets": forms.Textarea(attrs={"rows": 4})}


class RedirectForm(PanelForm):
    class Meta:
        model = Redirect
        fields = ["from_path", "to_url", "permanent", "is_active"]

    def clean_from_path(self):
        value = self.cleaned_data["from_path"].strip()
        if not value.startswith("/"):
            raise forms.ValidationError("نشانی باید با / شروع شود.")
        return value


class MediaMetaForm(PanelForm):
    class Meta:
        model = Media
        fields = ["title", "alt"]


# -- settings, one form per tab --------------------------------------------------------

SETTINGS_TABS = [
    ("general", "عمومی", ["site_name", "tagline", "description", "default_og_image", "footer_note", "copyright_text"]),
    ("home", "صفحهٔ اصلی", ["hero_title", "hero_highlight", "hero_text", "hero_primary_label", "hero_primary_url",
                           "hero_secondary_label", "hero_secondary_url", "featured_plan_slug"]),
    ("bar", "نوار اطلاعیه", ["bar_enabled", "bar_text", "bar_link_text", "bar_url"]),
    ("contact", "تماس و شبکه‌ها", ["contact_email", "contact_phone", "address", "telegram_url", "instagram_url", "linkedin_url", "youtube_url", "x_url"]),
    ("features", "امکانات", ["comments_enabled", "comments_moderated", "newsletter_enabled", "posts_per_page"]),
    ("seo", "سئو", ["title_suffix", "google_verification", "bing_verification", "robots_extra", "noindex_site", "analytics_head"]),
    ("maintenance", "تعمیر", ["maintenance_mode", "maintenance_text"]),
]


def settings_form_class(fields):
    _fields = list(fields)

    class _Form(PanelForm):
        class Meta:
            model = SiteSettings
            fields = _fields
            widgets = {"description": forms.Textarea(attrs={"rows": 3}), "hero_text": forms.Textarea(attrs={"rows": 3}),
                       "robots_extra": forms.Textarea(attrs={"rows": 4, "dir": "ltr"}), "analytics_head": forms.Textarea(attrs={"rows": 5, "dir": "ltr"})}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if "default_og_image" in self.fields:
                self.fields["default_og_image"].queryset = Media.objects.filter(content_type__startswith="image/")
                self.fields["default_og_image"].required = False

    return _Form


class StaffAddForm(StyledFormMixin, forms.Form):
    from ..models import StaffRole as _R

    identifier = forms.CharField(label="شمارهٔ موبایل، ایمیل یا نام کاربری", widget=forms.TextInput(attrs={"dir": "ltr"}))
    role = forms.ChoiceField(label="نقش", choices=_R.ROLE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
