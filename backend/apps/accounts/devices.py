"""Device labels and proxy-aware address extraction, without fingerprinting."""

import ipaddress
import re

from django.conf import settings
from django.utils import timezone


def client_ip(request):
    if request is None:
        return None
    try:
        peer = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None
    trusted = []
    for value in settings.CLIENT_IP_TRUSTED_PROXIES.split(","):
        try:
            trusted.append(ipaddress.ip_network(value.strip()))
        except ValueError:
            continue
    if not any(peer in network for network in trusted):
        return str(peer)
    chain = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    for value in reversed(chain):
        try:
            address = ipaddress.ip_address(value.strip())
        except ValueError:
            return str(peer)
        if not any(address in network for network in trusted):
            return str(address)
    return str(peer)


def device_details(request):
    meta = request.META if request is not None else {}
    ua = meta.get("HTTP_USER_AGENT", "")[:255]
    platform = meta.get("HTTP_X_CLIENT_PLATFORM", "").lower()
    if platform not in {"android", "ios", "web"}:
        platform = "web"
    os_name, os_version = "Unknown", ""
    patterns = [
        ("Android", r"Android[ /]([\d.]+)"),
        ("iOS", r"(?:CPU (?:iPhone )?OS|iPhone OS) ([\d_]+)"),
        ("Windows", r"Windows NT ([\d.]+)"),
        ("macOS", r"Mac OS X[ /]([\d_]+)"),
        ("ChromeOS", r"CrOS \S+ ([\d.]+)"),
    ]
    for name, pattern in patterns:
        match = re.search(pattern, ua, re.I)
        if match:
            os_name, os_version = name, match[1].replace("_", ".")
            break
    if os_name == "Unknown" and "Linux" in ua:
        os_name = "Linux"
    if platform in {"android", "ios"}:
        os_name = "Android" if platform == "android" else "iOS"
        os_version = meta.get("HTTP_X_DEVICE_OS_VERSION", os_version)[:40]
    browser = ""
    for name, pattern in [("Edge", r"Edg(?:A|iOS)?/"), ("Firefox", r"(?:Firefox|FxiOS)/"), ("Chrome", r"(?:Chrome|CriOS)/"), ("Safari", r"Safari/")]:
        if re.search(pattern, ua):
            browser = name
            break
    is_tablet = bool(re.search(r"iPad|Tablet", ua, re.I)) or ("Android" in ua and "Mobile" not in ua)
    device_type = "tablet" if is_tablet else "phone" if platform != "web" or re.search(r"Mobile|iPhone", ua, re.I) else "desktop"
    device_id = (meta.get("HTTP_X_DEVICE_ID") or getattr(request, "browser_device_id", "") or (request.COOKIES.get("pharmenta.device", "") if request is not None else ""))[:64]
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", device_id):
        device_id = ""
    return {"os_name": os_name, "os_version": os_version, "browser": browser,
            "device_type": device_type, "client_platform": platform, "device_id": device_id}


def touch_session(session, request, *, force=False):
    from .models import SessionAddress, UserSession

    now = timezone.now()
    address = client_ip(request)
    if force or (now - session.last_used_at).total_seconds() >= 60 or address != session.ip_address:
        details = device_details(request)
        # An existing token is a session on its original platform; never relabel it
        # as "web" merely because a renewal request has no native headers.
        details.pop("device_id")
        if not request.META.get("HTTP_X_CLIENT_PLATFORM"):
            details.pop("client_platform")
        updates = {"last_used_at": now}
        if address:
            updates["ip_address"] = address
            SessionAddress.objects.update_or_create(session=session, ip_address=address, defaults={"last_seen_at": now})
        if request.META.get("HTTP_USER_AGENT"):
            updates["user_agent"] = request.META["HTTP_USER_AGENT"][:255]
        updates.update({k: v for k, v in details.items() if v and v != "Unknown"})
        UserSession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(**updates)
        for name, value in updates.items():
            setattr(session, name, value)
