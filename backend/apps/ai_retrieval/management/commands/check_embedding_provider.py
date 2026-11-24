import json
from contextlib import nullcontext
from uuid import UUID
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings
from apps.ai_lab.provider import ProviderError
from apps.ai_retrieval.embeddings import embed, profile, profile_status


class Command(BaseCommand):
    help = "Make one tiny embedding capability test; never print credentials, vectors or provider error bodies."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--generation", type=UUID,
                          help="Compare a job's generation to the worker without opening the raw source.")
        group.add_argument("--active-index", action="store_true",
                            help="Compare active index and worker configuration without a provider request.")
        parser.add_argument("--reuse-chat-key", action="store_true")

    def handle(self, *args, **options):
        try:
            if options["active_index"] or options["generation"]:
                from apps.ai_retrieval.models import RetrievalHead
                from apps.ai_lab.reference_index import source_stamp
                heads = RetrievalHead.objects.select_related("active")
                if options["generation"]:
                    head = heads.filter(active_id=options["generation"]).first()
                else:
                    head = heads.filter(pk=source_stamp().identity).first()
                if not head or not head.active:
                    raise CommandError("HYBRID_INDEX_NOT_READY")
                status = profile_status(head.active)
                self.stdout.write(json.dumps({"generation": str(head.active_id), **status}))
                if not status["ready"]:
                    raise CommandError(status["code"])
                return
            with override_settings(AI_LAB_EMBEDDING_USE_CHAT_KEY=True) if options["reuse_chat_key"] else nullcontext():
                vectors, metadata = embed(["nocturnal enuresis in children", "amoxicillin dosing"])
                self.stdout.write(json.dumps({"ok": True, "model": profile()["model"],
                    "dimensions": len(vectors[0]), "returned_inputs": len(vectors), **metadata}))
        except ProviderError as exc:
            raise CommandError(f"{exc.code} status={exc.status}") from None
