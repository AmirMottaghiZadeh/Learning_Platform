from django import template

register = template.Library()


@register.filter
def dict_get(mapping, key):
    """`{{ some_dict|dict_get:dynamic_key }}` -- Django's dot lookup only
    takes a literal key written in the template, not another template
    variable, so a dict keyed by a per-row value (e.g. a section's field
    name) needs this instead."""
    return mapping.get(key)
