"""The encrypted package format the app downloads to read UpToDate and
Lexicomp without the network.

A package is a few large part files plus a plaintext manifest. Every record
inside the parts -- an article, an image, an interaction text, and the index
that locates all of them -- is sealed on its own with AES-256-GCM:

    record = nonce (12 bytes) || ciphertext || tag (16 bytes)

so the app can read and open any one record by offset, and nothing in the
files is readable without the package key. JSON and text records are
zlib-compressed before sealing; images are sealed as they are.

Each build has its own key, derived from OFFLINE_PACKAGE_SECRET and the
build id, so the server can hand the key to an entitled app without
storing it anywhere. The app gets it only from the license endpoint.

Layout written by `PackWriter` (and uploaded to the bucket as it is):

    <dataset>/latest.json            -- the manifest of the current build
    <dataset>/<build>/part-000.bin   -- records, ~100 MB each
    ...

The manifest names the parts (size, sha256), where the index record sits
([part, offset, length]) and a small sealed "check" record so the app can
tell a wrong key from a damaged file.
"""

import hashlib
import hmac
import json
import os
import secrets
import zlib
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

FORMAT = 1
NONCE_BYTES = 12
CHECK_PLAINTEXT = b"pharmenta-offline"
DEFAULT_PART_BYTES = 100 * 1024 * 1024
DATASETS = ("uptodate", "lexicomp")


class PackError(RuntimeError):
    pass


def secret() -> bytes:
    value = getattr(settings, "OFFLINE_PACKAGE_SECRET", "")
    if not value:
        raise PackError("OFFLINE_PACKAGE_SECRET is not configured.")
    return value.encode()


def derive_key(build: str) -> bytes:
    """The 32-byte AES key of one build."""
    return hmac.new(secret(), f"pharmenta-offline-v{FORMAT}:{build}".encode(), hashlib.sha256).digest()


def new_build_id(dataset: str, source_version: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{dataset}-{source_version or 'v'}-{stamp}-{secrets.token_hex(3)}"


def build_matches_dataset(build: str, dataset: str) -> bool:
    return (
        isinstance(build, str)
        and build.startswith(f"{dataset}-")
        and len(build) <= 80
        and all(c.isalnum() or c in "-_." for c in build)
    )


def seal(key: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(NONCE_BYTES)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, None)


def open_sealed(key: bytes, record: bytes) -> bytes:
    return AESGCM(key).decrypt(record[:NONCE_BYTES], record[NONCE_BYTES:], None)


def pack_json(value) -> bytes:
    return zlib.compress(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(), 6)


def pack_text(value: str) -> bytes:
    return zlib.compress(value.encode(), 6)


class PackWriter:
    """Appends sealed records to part files under `<out>/<dataset>/<build>/`;
    `finish()` seals the index and writes the manifest."""

    def __init__(self, out_dir, dataset: str, source_version: str, part_bytes: int = DEFAULT_PART_BYTES):
        self.dataset = dataset
        self.source_version = str(source_version or "")
        self.build = new_build_id(dataset, self.source_version)
        self.key = derive_key(self.build)
        self.part_bytes = part_bytes
        self.root = Path(out_dir) / dataset
        self.dir = self.root / self.build
        self.dir.mkdir(parents=True, exist_ok=False)
        self._parts: list[Path] = []
        self._fh = None
        self._size = 0
        self.records = 0

    def _open_part(self):
        if self._fh is not None:
            self._fh.close()
        path = self.dir / f"part-{len(self._parts):03d}.bin"
        self._parts.append(path)
        self._fh = path.open("wb")
        self._size = 0

    def add(self, plaintext: bytes) -> list[int]:
        """Seal one record; returns its locator [part, offset, length]."""
        record = seal(self.key, plaintext)
        if self._fh is None or (self._size and self._size + len(record) > self.part_bytes):
            self._open_part()
        offset = self._size
        self._fh.write(record)
        self._size += len(record)
        self.records += 1
        return [len(self._parts) - 1, offset, len(record)]

    def finish(self, index) -> dict:
        index_loc = self.add(pack_json(index))
        self._fh.close()
        self._fh = None
        files = []
        for path in self._parts:
            # md5 too: the phone app checks a downloaded part with the
            # platform's own md5 rather than hashing 100 MB in script.
            sha, md5 = hashlib.sha256(), hashlib.md5()
            with path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    sha.update(chunk)
                    md5.update(chunk)
            files.append({
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": sha.hexdigest(),
                "md5": md5.hexdigest(),
            })
        manifest = {
            "format": FORMAT,
            "dataset": self.dataset,
            "build": self.build,
            "source_version": self.source_version,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": files,
            "total_size": sum(f["size"] for f in files),
            "index": index_loc,
            "records": self.records,
            "check": seal(self.key, CHECK_PLAINTEXT).hex(),
        }
        text = json.dumps(manifest, indent=2)
        (self.dir / "manifest.json").write_text(text)
        (self.root / "latest.json").write_text(text)
        return manifest


def read_record(build_dir, key: bytes, locator) -> bytes:
    part, offset, length = locator
    with (Path(build_dir) / f"part-{part:03d}.bin").open("rb") as fh:
        fh.seek(offset)
        return open_sealed(key, fh.read(length))
