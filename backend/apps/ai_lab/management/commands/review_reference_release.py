import json
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, review


class Command(BaseCommand):
    help = "Create an offline private clinical-review worksheet; no provider requests or approvals."

    def add_arguments(self, parser):
        parser.add_argument("--input", action="append", required=True, dest="inputs")
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            html = review.worksheet([json.loads(Path(path).read_text()) for path in options["inputs"]])
            if re.search(r"sk-[A-Za-z0-9_-]{16,}", html):
                raise evaluation.EvaluationError("CREDENTIAL_IN_REPORT")
            target = Path(options["output"])
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as handle:
                handle.write(html)
            self.stdout.write("Private review worksheet created; no responses were approved.")
        except evaluation.EvaluationError as error:
            raise CommandError(str(error)) from None
        except Exception:
            raise CommandError("REVIEW_WORKSHEET_FAILED") from None
