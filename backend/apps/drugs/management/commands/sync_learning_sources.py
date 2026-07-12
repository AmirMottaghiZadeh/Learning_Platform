from django.core.management.base import BaseCommand

from apps.drugs.learning_sync import sync_all_drug_question_sources


class Command(BaseCommand):
    help = "Sync Pharmexa drug question sources into generic platform learning sources."

    def handle(self, *args, **options):
        result = sync_all_drug_question_sources()
        self.stdout.write(
            self.style.SUCCESS(
                "Synced learning sources: "
                f"{result.topics} topics, "
                f"{result.learning_objects} learning objects, "
                f"{result.knowledge_sources} knowledge sources."
            )
        )
