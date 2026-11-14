from django.core.management.commands.runserver import Command as RunServerCommand

from apps.ai_lab.warmup import warm_search


class Command(RunServerCommand):
    help = "Run the local API with optional reference-search warmup in the serving process."

    def inner_run(self, *args, **options):
        warm_search()
        return super().inner_run(*args, **options)
