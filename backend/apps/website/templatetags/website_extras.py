from django import template

from apps.drugs.data.atc_reference import ATC_L1

register = template.Library()


@register.filter
def on_site(path):
    """A site path ("/blog/x/") as a full address on the site, for links from
    the admin, which lives on another domain."""
    from .. import services

    return services.absolute(path) if isinstance(path, str) and path.startswith("/") else path


@register.filter
def post_link(post):
    """A post's address on the site; a draft's opens as a preview."""
    from .. import services

    return services.post_link(post)


@register.simple_tag
def atc_groups():
    """[(code, Persian name)] for the 14 anatomical ATC groups."""
    return [(code, names[1]) for code, names in ATC_L1.items()]


# A feature card's title picks the app's own icon for it, so cards keep the
# right picture when editors reorder or reword them; first match wins.
FEATURE_ICONS = (
    ("فلش", "edu-flashcards"), ("لایتنر", "edu-flashcards"), ("آزمون", "edu-quiz"),
    ("ماشین", "entry-calculator"), ("محاسبه", "entry-calculator"), ("بیماری", "entry-diseases"),
    ("راهنما", "entry-guidelines"), ("درس", "edu-lessons"), ("ATC", "edu-lessons"),
)


@register.filter
def feature_icon(title):
    """Static path of the app icon that fits a feature title, or ""."""
    for word, name in FEATURE_ICONS:
        if word in (title or ""):
            return f"website/img/{name}.png"
    return ""


@register.simple_tag
def nav_on(path, url):
    """True when `url` is the current section of the site."""
    if not url or url.startswith(("http://", "https://")):
        return False
    return path == url or (url != "/" and path.startswith(url))


@register.filter
def split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


@register.filter
def split_highlight(title, word):
    """The hero title as safe HTML with `word` wrapped in <b>."""
    from django.utils.html import escape
    from django.utils.safestring import mark_safe

    before, _, after = title.partition(word)
    return [mark_safe(f"{escape(before)}<b>{escape(word)}</b>{escape(after)}")]


@register.filter
def person(user):
    """A user's full name, else their username, else a dash."""
    if user is None:
        return "—"
    return user.get_full_name() or user.get_username() or "—"


@register.filter
def oneline(value):
    """Text on one line with single spaces: what a meta description (typed in
    the panel, maybe over several lines) should be."""
    return " ".join(str(value or "").split())
