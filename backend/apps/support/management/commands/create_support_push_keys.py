"""Create a stable local VAPID identity without printing private material."""

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create Web Push signing keys; optionally configure the local backend .env. Never overwrites a key."

    def add_arguments(self, parser):
        parser.add_argument("--out-dir", default=str(settings.BASE_DIR / ".private"))
        parser.add_argument("--configure-local", action="store_true")

    def handle(self, *args, **options):
        root = Path(options["out_dir"]).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        private = root / "support-vapid.pem"
        if private.exists():
            key = serialization.load_pem_private_key(private.read_bytes(), password=None)
        else:
            key = ec.generate_private_key(ec.SECP256R1())
            fd = os.open(private, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        public = base64.urlsafe_b64encode(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)).decode().rstrip("=")
        (root / "support-vapid-public.txt").write_text(public + "\n")
        if options["configure_local"]:
            env = settings.BASE_DIR / ".env"
            content = env.read_text() if env.exists() else ""
            existing = {line.split("=", 1)[0].strip(): line.split("=", 1)[1].strip() for line in content.splitlines() if "=" in line and not line.lstrip().startswith("#")}
            values = {"SUPPORT_WEB_PUSH_PRIVATE_KEY": str(private), "SUPPORT_WEB_PUSH_PUBLIC_KEY": public, "SUPPORT_WEB_PUSH_SUBJECT": "mailto:support@pharmenta.ir"}
            if any(name in existing and existing[name] and existing[name] != value for name, value in values.items()):
                raise CommandError("Existing Web Push settings differ. Keep the existing signing identity; no .env value was changed.")
            lines = [line for line in content.splitlines() if line.split("=", 1)[0].strip() not in values]
            env.write_text("\n".join(lines).rstrip() + "\n\n# Support Web Push\n" + "\n".join(f"{name}={value}" for name, value in values.items()) + "\n")
            env.chmod(0o600)
        self.stdout.write(self.style.SUCCESS("Web Push keys are ready. Private material was not printed."))
        self.stdout.write(f"Key directory: {root}")
        if options["configure_local"]:
            self.stdout.write("Local .env configured. Restart the backend to load the keys.")
