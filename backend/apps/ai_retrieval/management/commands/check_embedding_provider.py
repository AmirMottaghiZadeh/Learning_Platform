import json
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings
from apps.ai_lab.provider import ProviderError
from apps.ai_retrieval.embeddings import embed, profile


class Command(BaseCommand):
    help = "Make one tiny embedding capability test; never print credentials, vectors or provider error bodies."

    def add_arguments(self, parser):
        parser.add_argument("--reuse-chat-key", action="store_true")

    def handle(self, *args, **options):
        try:
            with override_settings(AI_LAB_EMBEDDING_USE_CHAT_KEY=options["reuse_chat_key"]):
                vectors, metadata = embed(["nocturnal enuresis in children", "amoxicillin dosing"])
                self.stdout.write(json.dumps({"ok": True, "model": profile()["model"],
                    "dimensions": len(vectors[0]), "returned_inputs": len(vectors), **metadata}))
        except ProviderError as exc:
            raise CommandError(f"{exc.code} status={exc.status}") from None
