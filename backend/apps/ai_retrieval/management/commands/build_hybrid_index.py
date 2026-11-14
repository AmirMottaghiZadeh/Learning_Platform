import json
from django.core.management.base import BaseCommand, CommandError
from apps.ai_retrieval import indexing
from apps.ai_retrieval.models import RetrievalGeneration


class Command(BaseCommand):
    help = "Build resumable clinical chunks and source tagging from the prepared reference generation. No paid API calls."

    def add_arguments(self, parser):
        parser.add_argument("--limit-articles", type=int)
        parser.add_argument("--article-ids", default="")
        parser.add_argument("--resume")
        parser.add_argument("--manifest", metavar="GENERATION")
        parser.add_argument("--status", action="store_true")

    def handle(self, *args, **options):
        stage = "arguments"
        try:
            if options["limit_articles"] is not None and options["limit_articles"] < 1:
                raise CommandError("limit-articles must be positive.")
            if options["manifest"]:
                stage = "manifest"
                result = indexing.manifest(RetrievalGeneration.objects.get(pk=options["manifest"]))
            elif options["status"]:
                result = list(RetrievalGeneration.objects.order_by("-created_at").values(
                    "id", "scope", "status", "built_articles", "expected_articles", "chunk_count", "embedding_ready")[:5])
            else:
                stage = "build"
                generation = indexing.build(limit=options["limit_articles"],
                    identifiers=[v.strip() for v in options["article_ids"].split(",") if v.strip()],
                    resume=options["resume"],
                    progress=lambda row: self.stdout.write(json.dumps(row)))
                result = indexing.manifest(generation)
            self.stdout.write(json.dumps(result, default=str))
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"HYBRID_INDEX_FAILED stage={stage} code={getattr(exc, 'code', 'INTERNAL_ERROR')} type={type(exc).__name__}") from None
