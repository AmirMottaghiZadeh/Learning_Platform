"""Build, verify and document the files for a manual Object Storage upload."""

import zlib

from cryptography.exceptions import InvalidTag
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.offline.builders import BUILDERS
from apps.offline.pack import PackError
from apps.offline.upload import prepare_upload


class Command(BaseCommand):
    help = "Build and verify an offline package, then write its manual upload guide. Does not upload."

    def add_arguments(self, parser):
        parser.add_argument("dataset", choices=sorted(BUILDERS))
        parser.add_argument("--out", required=True, help="Local package root directory.")
        parser.add_argument("--source", default="", help="SQLite snapshot directory; defaults to the dataset setting.")
        parser.add_argument("--part-size-mb", type=int, default=100)
        parser.add_argument("--existing", action="store_true", help="Verify the existing latest.json build without rebuilding.")

    def handle(self, *args, dataset, out, source, part_size_mb, existing, **options):
        if existing and source:
            raise CommandError("--existing reads the existing package; omit --source.")
        if not existing:
            call_command(
                "build_offline_package", dataset, out=out, source=source,
                part_size_mb=part_size_mb, stdout=self.stdout, stderr=self.stderr,
            )
        try:
            manifest, build_dir, guide = prepare_upload(dataset, out)
        except InvalidTag:
            raise CommandError("The package cannot be decrypted with the configured OFFLINE_PACKAGE_SECRET.")
        except (OSError, ValueError, KeyError, TypeError, IndexError, zlib.error, PackError) as exc:
            raise CommandError(f"Package not ready for upload: {exc}")
        self.stdout.write(self.style.SUCCESS(
            f"Ready: {manifest['build']}; {len(manifest['files'])} verified part(s), {manifest['total_size']:,} bytes."
        ))
        self.stdout.write(f"1. Upload {build_dir}/ to <bucket>/{dataset}/{manifest['build']}/")
        self.stdout.write(f"2. Upload {build_dir.parent / 'latest.json'} to <bucket>/{dataset}/latest.json LAST")
        self.stdout.write(f"Guide: {guide}")
