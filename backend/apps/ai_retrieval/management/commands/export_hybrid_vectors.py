import json

from django.core.management.base import BaseCommand, CommandError
from apps.ai_retrieval.models import RetrievalGeneration
from apps.ai_retrieval.portable_vectors import export_vectors


class Command(BaseCommand):
    help = "Export private, portable input-hash/vector data without users, text, keys or paid requests."

    def add_arguments(self, parser):
        parser.add_argument("generation")
        parser.add_argument("--output", required=True)
        parser.add_argument("--batch-size", type=int, default=256)

    def handle(self, *args, **options):
        try:
            if not 1<=options["batch_size"]<=1024:
                raise ValueError
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            result = export_vectors(generation,options["output"],batch_size=options["batch_size"],
                progress=lambda row:self.stdout.write(json.dumps(row)))
            self.stdout.write(json.dumps(result))
        except Exception as exc:
            raise CommandError(f"VECTOR_EXPORT_FAILED code={getattr(exc,'code','INVALID_EXPORT')} type={type(exc).__name__}") from None
