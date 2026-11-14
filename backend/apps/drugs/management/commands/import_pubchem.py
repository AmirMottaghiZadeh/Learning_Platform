from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.models import Q
from apps.drugs.chemistry import ChemistryError, enrich, version
from apps.drugs.models import Ingredient


class Command(BaseCommand):
    help = "Fetch validated PubChem chemistry (visible by default); never mark it manually approved. Skips existing rows."

    def add_arguments(self, parser):
        parser.add_argument("--rxcui", action="append", help="Restrict to this RxCUI (repeatable)")
        parser.add_argument("--limit", type=int, default=0, help="0 = all missing records")
        parser.add_argument("--workers", type=int, default=1, choices=range(1, 5))

    def handle(self, *args, **options):
        if options["limit"] < 0:
            raise CommandError("limit must be >= 0")
        qs = Ingredient.objects.filter(Q(chemistry__isnull=True) | Q(
            chemistry__ingredient_name="", chemistry__status="pending",
        )).select_related("chemistry").order_by("pk")
        if options["rxcui"]:
            qs = qs.filter(rxcui__in=options["rxcui"])
        if options["limit"]:
            qs = qs[:options["limit"]]

        def process(ingredient):
            try:
                result = enrich(ingredient, expected=version(getattr(ingredient, "chemistry", None)))
                return ingredient.rxcui, result.status, False
            except ChemistryError as exc:
                return ingredient.rxcui, str(exc), True
            finally:
                if options["workers"] > 1:
                    connections.close_all()

        done = errors = 0
        ingredients = list(qs)
        pool = ThreadPoolExecutor(max_workers=options["workers"])

        def results():
            if options["workers"] == 1:
                yield from map(process, ingredients)
                return
            iterator = iter(ingredients)
            pending = {pool.submit(process, item) for item in [next(iterator, None) for _ in range(options["workers"])] if item}
            while pending:
                complete, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in complete:
                    yield future.result()
                    item = next(iterator, None)
                    if item:
                        pending.add(pool.submit(process, item))

        try:
            for rxcui, status, failed in results():
                if not failed:
                    done += 1
                    self.stdout.write(f"{rxcui}: {status}")
                    continue
                errors += 1
                self.stderr.write(f"{rxcui}: {status}")
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
        self.stdout.write(f"Processed {done}; errors {errors}. No candidates auto-approved.")
        if errors:
            raise CommandError(f"{errors} compounds could not be processed; inspect the reported RxCUIs and resume or review manually.")
