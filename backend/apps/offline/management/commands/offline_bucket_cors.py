"""Set the bucket's CORS rule for the web app's downloads, then check it the
way a browser will.

    manage.py offline_bucket_cors
    manage.py offline_bucket_cors --show

The web app downloads the parts straight from the bucket with fetch(), so the
bucket must allow GET (with a Range header, to resume) from the app's origin.
Uses the OFFLINE_S3_* settings; nothing else is needed.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.offline import storage

DEFAULT_ORIGIN = "https://app.pharmenta.ir"


def cors_rule(origins: list[str]) -> dict:
    return {
        "AllowedOrigins": origins,
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedHeaders": ["Range"],
        "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
        "MaxAgeSeconds": 3600,
    }


def _request(url: str, method: str, headers: dict) -> tuple[int, dict]:
    request = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}
    except (urllib.error.URLError, OSError):
        return 0, {}


class Command(BaseCommand):
    help = "Set the offline bucket's CORS rule for the web app and check it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--origin",
            action="append",
            dest="origins",
            help=f"Allowed web app origin; repeat for more (default {DEFAULT_ORIGIN}).",
        )
        parser.add_argument("--show", action="store_true", help="Only print the current rule and check it.")

    def handle(self, *args, origins, show, **options):
        from botocore.exceptions import BotoCoreError, ClientError

        if not storage.using_s3():
            raise CommandError("Set OFFLINE_S3_ENDPOINT_URL, OFFLINE_S3_BUCKET and the access keys first.")
        origins = origins or [DEFAULT_ORIGIN]
        bucket = settings.OFFLINE_S3_BUCKET
        client = storage._s3()

        if not show:
            try:
                client.put_bucket_cors(Bucket=bucket, CORSConfiguration={"CORSRules": [cors_rule(origins)]})
            except ClientError as exc:
                error = exc.response.get("Error", {})
                raise CommandError(
                    f"The bucket refused the CORS rule ({error.get('Code')}: {error.get('Message')}). "
                    "If the storage panel has a CORS setting, set it there instead."
                )
            except BotoCoreError as exc:
                raise CommandError(f"Could not reach the bucket: {exc}")
            self.stdout.write(self.style.SUCCESS(f"CORS rule set on {bucket}."))

        try:
            rules = client.get_bucket_cors(Bucket=bucket).get("CORSRules", [])
        except ClientError as exc:
            rules = []
            self.stdout.write(self.style.WARNING(f"No CORS rule on {bucket} ({exc.response.get('Error', {}).get('Code')})."))
        except BotoCoreError as exc:
            raise CommandError(f"Could not reach the bucket: {exc}")
        if rules:
            self.stdout.write(json.dumps(rules, indent=2))

        key = storage._prefix() + "uptodate/latest.json"
        url = client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=300)
        origin = origins[0]

        # What a browser asks before a resumed (Range) download.
        status, headers = _request(
            url,
            "OPTIONS",
            {"Origin": origin, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "range"},
        )
        allowed = 200 <= status < 300 and headers.get("access-control-allow-origin") in (origin, "*")
        self._report(allowed, f"Preflight from {origin}: HTTP {status}, allow-origin={headers.get('access-control-allow-origin')}")

        status, headers = _request(url, "GET", {"Origin": origin, "Range": "bytes=0-0"})
        if status == 404:
            self.stdout.write(f"{key} is not uploaded yet; upload it and run --show to check a real download.")
        else:
            allowed = status in (200, 206) and headers.get("access-control-allow-origin") in (origin, "*")
            self._report(allowed, f"Signed download from {origin}: HTTP {status}, allow-origin={headers.get('access-control-allow-origin')}")

        # Without a signature the bucket should refuse: it is meant to be private.
        status, _ = _request(url.split("?", 1)[0], "GET", {"Range": "bytes=0-0"})
        if status in (200, 206):
            self.stdout.write(self.style.WARNING(f"The bucket is public (unsigned download: HTTP {status}); make it private."))
        elif status in (401, 403):
            self.stdout.write(self.style.SUCCESS(f"The bucket is private (unsigned download: HTTP {status})."))
        else:
            self.stdout.write(f"Unsigned download: HTTP {status}.")

    def _report(self, ok: bool, line: str):
        self.stdout.write(self.style.SUCCESS("OK   " + line) if ok else self.style.ERROR("FAIL " + line))
