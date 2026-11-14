import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, release


class Command(BaseCommand):
    help = "Check response-bound independent reviews and service/API/browser evidence before cohort rollout."

    def add_arguments(self, parser):
        parser.add_argument("--suite", required=True)
        parser.add_argument("--load")
        parser.add_argument("--browser")
        parser.add_argument("--reviews", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--approval-output")
        parser.add_argument("--expires-hours", type=float, default=24)

    def handle(self, *args, **options):
        def read(path):
            return json.loads(Path(path).read_text()) if path else None
        try:
            report = release.evaluate_gate(read(options["suite"]), read(options["load"]), read(options["browser"]), read(options["reviews"]))
            evaluation.write_private_json(options["output"], report)
            if options["approval_output"]:
                evaluation.write_private_json(options["approval_output"], release.approval(report, hours=options["expires_hours"]))
            self.stdout.write(f"Release decision: {report['decision']}; blockers={','.join(report['blockers'])}")
        except evaluation.EvaluationError as error:
            raise CommandError(str(error)) from None
        except Exception:
            raise CommandError("RELEASE_EVALUATION_FAILED") from None
