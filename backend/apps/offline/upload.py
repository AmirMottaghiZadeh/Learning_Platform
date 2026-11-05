"""Verify the local package tree and describe its manual upload order."""

import hashlib
import json
import zlib
from pathlib import Path

from .pack import CHECK_PLAINTEXT, FORMAT, PackError, build_matches_dataset, derive_key, open_sealed, read_record


def prepare_upload(dataset, out_dir):
    root = Path(out_dir).expanduser().resolve() / dataset
    manifest = json.loads((root / "latest.json").read_text())
    build = manifest["build"]
    if manifest["dataset"] != dataset or not build_matches_dataset(build, dataset) or manifest["format"] != FORMAT:
        raise PackError("The manifest does not describe a supported build of this dataset.")
    build_dir = root / build
    if json.loads((build_dir / "manifest.json").read_text()) != manifest:
        raise PackError("latest.json and the build's manifest.json differ.")
    parts = manifest["files"]
    if not parts or manifest["total_size"] != sum(part["size"] for part in parts):
        raise PackError("The manifest's part sizes do not add up.")
    for i, part in enumerate(parts):
        if part["name"] != f"part-{i:03d}.bin":
            raise PackError("The manifest contains an unexpected part name.")
        path = build_dir / part["name"]
        if path.stat().st_size != part["size"]:
            raise PackError(f"Wrong size: {part['name']}")
        sha, md5 = hashlib.sha256(), hashlib.md5()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(chunk)
                md5.update(chunk)
        if sha.hexdigest() != part["sha256"] or md5.hexdigest() != part["md5"]:
            raise PackError(f"Checksum mismatch: {part['name']}")

    key = derive_key(build)
    if open_sealed(key, bytes.fromhex(manifest["check"])) != CHECK_PLAINTEXT:
        raise PackError("The package's check record is invalid.")
    index = json.loads(zlib.decompress(read_record(build_dir, key, manifest["index"])))
    if index.get("dataset") != dataset:
        raise PackError("The encrypted index belongs to another dataset.")
    if dataset == "uptodate" and (
        index.get("search_schema") != 1
        or not index.get("search", {}).get("queries")
        or not index.get("search", {}).get("topics")
        or len(index.get("topics", {}).get("memberships", [])) != len(index.get("topics", {}).get("ids", []))
    ):
        raise PackError("UpToDate concept metadata is missing. Rebuild from a snapshot containing search.db.")

    guide = root / "UPLOAD.fa.md"
    guide.write_text(
        f"# آمادهٔ آپلود: {build}\n\n"
        f"حجم قطعه‌ها: {manifest['total_size']:,} بایت؛ تعداد: {len(parts)}.\n\n"
        f"۱. تمام فایل‌های این پوشه (قطعه‌ها و manifest.json) را آپلود کنید:\n\n"
        f"    {build_dir}/\n\n"
        f"مسیر مقصد، زیر پیشوند فعلی داده‌های آفلاین باکت:\n\n"
        f"    {dataset}/{build}/\n\n"
        f"۲. فقط پس از پایان آپلود همهٔ قطعه‌ها، این فایل را جایگزین کنید:\n\n"
        f"    {root / 'latest.json'}\n\n"
        f"مسیر مقصد: {dataset}/latest.json\n\n"
        "اندازه، SHA-256 و MD5 همهٔ قطعه‌ها و رمزگشایی index بررسی شدند. "
        "این بررسی شامل رمزگشایی تک‌تک مقاله‌ها نیست.\n\n"
        "این دستور فایل‌ها را روی سرور آپلود نمی‌کند. پوشهٔ قبلی را برای دانلودهای در جریان نگه دارید. "
        "کش manifest سرور پنج دقیقه است. این راهنما، دیتابیس خام و فایل env جزو فایل‌های دانلود کاربر نیستند.\n\n"
        "برای جست‌وجوی مفهومی UpToDate، کلاینت به‌روز اپ هم باید منتشر شود. "
        "OFFLINE_PACKAGE_SECRET سرور و زمان ساخت باید یکسان بماند.\n",
        encoding="utf-8",
    )
    return manifest, build_dir, guide
