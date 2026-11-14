"""Who may keep a package on their device, and the license that lets the app
open it.

A package can be downloaded and opened only by a learner with a *paid* plan
that includes the dataset's feature (and by staff) -- whether or not billing
enforcement is on, unlike the online gates. Offline reading is not counted
against the feature's cap.

The license carries the build's key and a `valid_until` OFFLINE_LICENSE_DAYS
ahead. The app renews it whenever it is online; once the date passes without
a renewal, or a renewal is refused, the app stops opening the package.

The key travels in one of two forms:
- raw (base64), for the Android/iOS app, which keeps it in the Keystore /
  Keychain;
- wrapped with RSA-OAEP-SHA256 to a public key the browser generated, for the
  web app/PWA: the browser unwraps it into a non-extractable key, so the raw
  key never shows up in a response or in page script.
"""

import base64
from datetime import timedelta

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings
from django.utils import timezone

from apps.billing import services as billing

from .pack import derive_key

# dataset -> the billing feature that sells it
FEATURE_FOR = {"uptodate": "uptodate", "lexicomp": "lexicomp"}


class LicenseError(ValueError):
    pass


def is_guest(user) -> bool:
    return hasattr(user, "guest_account")


def has_paid_plan_with(user, feature_key: str) -> bool:
    return any(
        not ent.plan.is_free and feature_key in (ent.features or {})
        for ent in billing.active_entitlements(user)
    )


def is_entitled(user, dataset: str) -> bool:
    if user is None or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if is_guest(user):
        return False
    return has_paid_plan_with(user, FEATURE_FOR[dataset])


def license_days() -> int:
    return int(getattr(settings, "OFFLINE_LICENSE_DAYS", 30))


def _wrap_for(public_key_b64: str, key: bytes) -> str:
    try:
        public_key = serialization.load_der_public_key(base64.b64decode(public_key_b64))
    except Exception as exc:
        raise LicenseError("public_key is not a base64 SPKI key.") from exc
    if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size < 2048:
        raise LicenseError("public_key must be an RSA key of at least 2048 bits.")
    wrapped = public_key.encrypt(
        key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return base64.b64encode(wrapped).decode("ascii")


def issue_license(build: str, public_key_b64: str = "") -> dict:
    now = timezone.now()
    key = derive_key(build)
    license = {
        "build": build,
        "server_time": now.isoformat(),
        "valid_until": (now + timedelta(days=license_days())).isoformat(),
    }
    if public_key_b64:
        license["wrapped_key"] = _wrap_for(public_key_b64, key)
    else:
        license["key"] = base64.b64encode(key).decode("ascii")
    return license
