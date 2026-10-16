from django import template

from apps.drugs.data.atc_reference import ATC_L1

register = template.Library()


@register.simple_tag
def atc_groups():
    """[(code, Persian name)] for the 14 anatomical ATC groups."""
    return [(code, names[1]) for code, names in ATC_L1.items()]


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
