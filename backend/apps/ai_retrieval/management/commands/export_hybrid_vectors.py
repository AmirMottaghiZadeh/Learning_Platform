import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from apps.ai_retrieval.models import RetrievalGeneration
from apps.ai_retrieval.portable_vectors import export_vectors
from apps.ai_retrieval.archive_parts import split_archive, MAX_PARTS


class Command(BaseCommand):
    help = "Export private, portable input-hash/vector data without users, text, keys or paid requests."

    def add_arguments(self, parser):
        parser.add_argument("generation")
        parser.add_argument("--output", required=True)
        parser.add_argument("--batch-size", type=int, default=256)
        parser.add_argument("--parts", type=int, help="After a successful export, split it into this many upload parts.")

    def handle(self, *args, **options):
        stage = "export"
        def report(value):
            self.stdout.write(json.dumps(value))
            self.stdout.flush()
        try:
            if not 1<=options["batch_size"]<=1024:
                raise ValueError
            if options["parts"] is not None:
                if not 2 <= options["parts"] <= MAX_PARTS:
                    raise CommandError(f"parts must be between 2 and {MAX_PARTS}.")
                if Path(str(options["output"]) + ".parts").exists():
                    raise CommandError("PARTS_DIRECTORY_EXISTS: choose a new output name or use the existing parts.")
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            result = export_vectors(generation,options["output"],batch_size=options["batch_size"],
                progress=report)
            report(result)
            if options["parts"] is not None:
                stage = "split"
                divided = split_archive(options["output"], parts=options["parts"], progress=report)
                report(divided)
        except CommandError:
            raise
        except Exception as exc:
            if stage == "split":
                raise CommandError(f"VECTOR_SPLIT_FAILED code={getattr(exc,'code','FILE_IO_ERROR')}; completed export preserved; use archive_parts.py split to retry.") from None
            raise CommandError(f"VECTOR_EXPORT_FAILED code={getattr(exc,'code','INVALID_EXPORT')} type={type(exc).__name__}") from None
