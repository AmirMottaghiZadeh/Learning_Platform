"""Where the built packages live and how the app is sent to them.

Production: a private S3-compatible bucket (Runflare Object Storage) holding
the tree `PackWriter` wrote, uploaded by hand:

    <OFFLINE_S3_PREFIX><dataset>/latest.json
    <OFFLINE_S3_PREFIX><dataset>/<build>/part-000.bin ...

The app downloads straight from the bucket with presigned GET links, so the
API server never streams the gigabyte itself.

Development: with OFFLINE_PACKAGES_DIR set instead, the same tree is read
from that local directory and served by `views.PackageFileView` behind a
signed, expiring token.
"""

import json
import time
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.urls import reverse

MANIFEST_CACHE_SECONDS = 300
FILE_TOKEN_SALT = "offline-package-file"
_manifests: dict[str, tuple[float, dict | None]] = {}


def _prefix() -> str:
    return getattr(settings, "OFFLINE_S3_PREFIX", "") or ""


def using_s3() -> bool:
    return bool(getattr(settings, "OFFLINE_S3_BUCKET", ""))


def local_dir() -> Path | None:
    value = getattr(settings, "OFFLINE_PACKAGES_DIR", "")
    return Path(value) if value else None


def is_configured() -> bool:
    return using_s3() or local_dir() is not None


def _s3():
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.OFFLINE_S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.OFFLINE_S3_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.OFFLINE_S3_SECRET_ACCESS_KEY or None,
        region_name=settings.OFFLINE_S3_REGION or None,
        config=Config(signature_version="s3v4", s3={"addressing_style": settings.OFFLINE_S3_ADDRESSING_STYLE}),
    )


def _read_manifest(dataset: str) -> dict | None:
    key = f"{dataset}/latest.json"
    if using_s3():
        try:
            body = _s3().get_object(Bucket=settings.OFFLINE_S3_BUCKET, Key=_prefix() + key)["Body"].read()
        except Exception:
            return None
    else:
        root = local_dir()
        path = root / key if root else None
        if path is None or not path.is_file():
            return None
        body = path.read_bytes()
    try:
        manifest = json.loads(body)
    except ValueError:
        return None
    return manifest if manifest.get("dataset") == dataset else None


def latest_manifest(dataset: str) -> dict | None:
    """The current build's manifest, or None when nothing is uploaded. Kept
    for a few minutes: a new upload shows up within MANIFEST_CACHE_SECONDS."""
    now = time.monotonic()
    cached = _manifests.get(dataset)
    if cached and now - cached[0] < MANIFEST_CACHE_SECONDS:
        return cached[1]
    manifest = _read_manifest(dataset) if is_configured() else None
    _manifests[dataset] = (now, manifest)
    return manifest


def clear_cache():
    _manifests.clear()


def file_urls(request, dataset: str, build: str, names: list[str], ttl: int) -> dict[str, str]:
    """{part name: a GET link valid for `ttl` seconds}."""
    keys = {name: f"{dataset}/{build}/{name}" for name in names}
    if using_s3():
        client = _s3()
        return {
            name: client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.OFFLINE_S3_BUCKET, "Key": _prefix() + key},
                ExpiresIn=ttl,
            )
            for name, key in keys.items()
        }
    return {
        name: request.build_absolute_uri(
            reverse("offline-package-file", args=[signing.dumps({"k": key}, salt=FILE_TOKEN_SALT)])
        )
        for name, key in keys.items()
    }


def local_file_for_token(token: str, ttl: int) -> Path | None:
    root = local_dir()
    if root is None:
        return None
    try:
        key = signing.loads(token, salt=FILE_TOKEN_SALT, max_age=ttl)["k"]
    except (signing.BadSignature, KeyError, TypeError):
        return None
    path = (root / key).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        return None
    return path
