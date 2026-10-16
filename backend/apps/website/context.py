def site(request):
    """Site settings and menus for the public templates; nothing for the API host."""
    if not getattr(request, "is_site", False):
        return {}
    from .models import MenuItem, SiteSettings

    settings_row = SiteSettings.get()
    menus = {}
    for item in MenuItem.objects.filter(is_active=True):
        menus.setdefault(item.location, []).append(item)
    return {"site": settings_row, "menus": menus}
