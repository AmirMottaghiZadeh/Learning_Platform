import json

from django.core.management.base import BaseCommand, CommandError
from apps.ai_retrieval.models import RetrievalGeneration
from apps.ai_retrieval.portable_vectors import import_vectors


class Command(BaseCommand):
    help = "Validate/map portable vectors to this server's chunks. Never calls an embedding API or activates search."

    def add_arguments(self, parser):
        parser.add_argument("generation")
        parser.add_argument("--input", required=True)
        parser.add_argument("--batch-size", type=int, default=256)
        parser.add_argument("--verify-only", action="store_true")
        parser.add_argument("--build-index", action="store_true")

    def handle(self, *args, **options):
        try:
            if not 1<=options["batch_size"]<=1024 or options["verify_only"] and options["build_index"]:
                raise ValueError
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            result = import_vectors(generation,options["input"],batch_size=options["batch_size"],
                verify_only=options["verify_only"],build_index=options["build_index"],
                progress=lambda row:self.stdout.write(json.dumps(row)))
            self.stdout.write(json.dumps(result))
        except Exception as exc:
            raise CommandError(f"VECTOR_IMPORT_FAILED code={getattr(exc,'code','INVALID_ARCHIVE')} type={type(exc).__name__}") from None
