import re

from django.db import migrations
from django.utils import timezone


def backfill(apps, schema_editor):
    Session = apps.get_model("accounts", "UserSession")
    Address = apps.get_model("accounts", "SessionAddress")
    Refresh = apps.get_model("accounts", "SessionRefreshToken")
    now = timezone.now()
    counts = {}
    for session in Session.objects.order_by("user_id", "-last_used_at", "-created_at").iterator(chunk_size=500):
        ua = session.user_agent
        os_name, version = "Unknown", ""
        for name, pattern in [("Android", r"Android[ /]([\d.]+)"), ("iOS", r"(?:CPU (?:iPhone )?OS|iPhone OS) ([\d_]+)"), ("Windows", r"Windows NT ([\d.]+)"), ("macOS", r"Mac OS X[ /]([\d_]+)")]:
            match = re.search(pattern, ua, re.I)
            if match:
                os_name, version = name, match[1].replace("_", ".")
                break
        browser = next((name for name, text in [("Edge", "Edg/"), ("Firefox", "Firefox/"), ("Chrome", "Chrome/"), ("Safari", "Safari/")] if text in ua), "")
        Session.objects.filter(pk=session.pk).update(os_name=os_name, os_version=version[:40], browser=browser, device_type="phone" if "Mobile" in ua or os_name in {"Android", "iOS"} else "desktop", client_platform="web" if browser else os_name.lower() if os_name in {"Android", "iOS"} else "")
        if session.ip_address:
            Address.objects.get_or_create(session_id=session.pk, ip_address=session.ip_address, defaults={"last_seen_at": session.last_used_at})
        if session.revoked_at is None and session.refresh_expires_at > now:
            used = counts.get(session.user_id, 0)
            counts[session.user_id] = used + 1
            if used >= 2:
                Session.objects.filter(pk=session.pk).update(revoked_at=now, revoke_reason="two_device_policy")
                Refresh.objects.filter(session_id=session.pk, revoked_at__isnull=True).update(revoked_at=now)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0007_usersession_browser_usersession_client_platform_and_more")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
