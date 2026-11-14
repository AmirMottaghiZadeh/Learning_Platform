import json
from django.core.management.base import BaseCommand,CommandError
from apps.ai_retrieval import indexing
from apps.ai_retrieval.models import RetrievalGeneration


class Command(BaseCommand):
    help="Clone fresh chunk/FTS/catalog data for a separate embedding model; never copies vectors or activates it."

    def add_arguments(self,parser):
        parser.add_argument("generation")
        parser.add_argument("--article-ids",default="")

    def handle(self,*args,**options):
        try:
            source=RetrievalGeneration.objects.get(pk=options["generation"])
            clone=indexing.clone_generation(source,identifiers=[i.strip() for i in options["article_ids"].split(",") if i.strip()],
                progress=lambda row:self.stdout.write(json.dumps(row)))
            self.stdout.write(json.dumps(indexing.manifest(clone)))
        except Exception as exc:
            raise CommandError(f"HYBRID_CLONE_FAILED code={getattr(exc,'code','INTERNAL_ERROR')} type={type(exc).__name__}") from None
