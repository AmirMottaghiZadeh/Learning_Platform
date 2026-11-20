from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.ai_lab.provider import ProviderError
from apps.ai_retrieval import indexing, vectors
from apps.ai_retrieval.models import RetrievalGeneration


class Command(BaseCommand):
    help = "Atomically activate a complete, fresh hybrid generation; also supports rollback to a compatible generation."

    def add_arguments(self, parser):
        parser.add_argument("generation")
        parser.add_argument("--lexical-pilot", action="store_true", help="Local platform-admin-only QA before bulk embeddings; never a public release.")

    def handle(self, *args, **options):
        lock = None
        try:
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            lock = indexing.reference_index.acquire_build_lock("hybrid-embed:"+str(generation.pk))
            if options["lexical_pilot"]:
                if settings.ENVIRONMENT != "local" or not settings.AI_LAB_LOCAL_LEXICAL_PILOT:
                    raise ProviderError("LOCAL_PILOT_MODE_REQUIRED")
                indexing.activate_generation(generation,require_embeddings=False)
                self.stdout.write(f"Local lexical pilot active={generation.pk}; platform admins only; not a semantic/public release.")
                return
            profile = vectors._configuration(generation)
            if vectors.count(generation, profile["id"]) != generation.chunk_count:
                raise ProviderError("HYBRID_EMBEDDINGS_INCOMPLETE")
            vectors.create_index(generation, profile)
            indexing.activate_generation(generation)
            self.stdout.write(f"Active hybrid generation={generation.pk}; chunks={generation.chunk_count}.")
        except Exception as exc:
            raise CommandError(f"HYBRID_ACTIVATION_FAILED code={getattr(exc, 'code', 'INTERNAL_ERROR')} type={type(exc).__name__}") from None
        finally:
            indexing.reference_index.release_build_lock(lock)
