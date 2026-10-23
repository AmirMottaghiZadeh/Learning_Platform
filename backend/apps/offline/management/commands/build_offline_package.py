"""Build an encrypted offline package from the local snapshot.

    manage.py build_offline_package uptodate --out ~/offline-packages
    manage.py build_offline_package lexicomp --out ~/offline-packages

Writes <out>/<dataset>/<build>/part-*.bin, manifest.json, and
<out>/<dataset>/latest.json. Upload <out>/<dataset>/<build>/ to the bucket
first and latest.json last: the app starts downloading whatever latest.json
names. Needs OFFLINE_PACKAGE_SECRET -- the same value the API server has.
"""

import json
import zlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.offline.builders import BUILDERS
from apps.offline.pack import CHECK_PLAINTEXT, PackError, derive_key, open_sealed, read_record


class Command(BaseCommand):
    help = "Build an encrypted offline package (uptodate or lexicomp) from the local SQLite snapshot."

    def add_arguments(self, parser):
        parser.add_argument("dataset", choices=sorted(BUILDERS))
        parser.add_argument("--out", required=True, help="Directory the package tree is written under.")
        parser.add_argument(
            "--source",
            default="",
            help="Snapshot directory (default: UPTODATE_DB_DIR / LEXICOMP_DB_DIR).",
        )
        parser.add_argument("--part-size-mb", type=int, default=100, help="Size of each part file (default 100).")

    def handle(self, *args, dataset, out, source, part_size_mb, **options):
        if not getattr(settings, "OFFLINE_PACKAGE_SECRET", ""):
            raise CommandError("Set OFFLINE_PACKAGE_SECRET (the same value as on the API server) first.")
        if part_size_mb < 1:
            raise CommandError("--part-size-mb must be at least 1.")
        source = source or (settings.UPTODATE_DB_DIR if dataset == "uptodate" else settings.LEXICOMP_DB_DIR)
        out_dir = Path(out).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            manifest = BUILDERS[dataset](source, out_dir, part_size_mb * 1024 * 1024, log=self.stdout.write)
        except FileNotFoundError as exc:
            raise CommandError(f"Snapshot file not found: {exc}")
        except PackError as exc:
            raise CommandError(str(exc))

        # Read the package back the way the app will before calling it done.
        build_dir = out_dir / dataset / manifest["build"]
        key = derive_key(manifest["build"])
        if open_sealed(key, bytes.fromhex(manifest["check"])) != CHECK_PLAINTEXT:
            raise CommandError("The package does not open with its own key.")
        index = json.loads(zlib.decompress(read_record(build_dir, key, manifest["index"])))
        if index.get("dataset") != dataset:
            raise CommandError("The package index does not read back.")

        mb = manifest["total_size"] / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f"Built {manifest['build']}: {len(manifest['files'])} part(s), {mb:.1f} MB, {manifest['records']} records."
        ))
        self.stdout.write(f"Upload {build_dir}/ to <bucket>/{dataset}/{manifest['build']}/,")
        self.stdout.write(f"then {out_dir / dataset / 'latest.json'} to <bucket>/{dataset}/latest.json (last).")
