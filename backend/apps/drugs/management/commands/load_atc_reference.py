"""Load the bundled bilingual ATC L1/L2 reference into drugs.AtcCategory.

Idempotent (matched on `code`). Warns about any L2 code that appears in the
imported ingredient data but has no reference row, and about reference rows for
L2 codes that no ingredient uses (harmless, just unused).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.drugs.data.atc_reference import ATC_L1, ATC_L2
from apps.drugs.models import AtcCategory, AtcCode


class Command(BaseCommand):
    help = "Load the ATC L1/L2 category reference."

    def handle(self, *args, **options):
        with transaction.atomic():
            l1_objs = {}
            for code, (name_en, name_fa) in ATC_L1.items():
                obj, _ = AtcCategory.objects.update_or_create(
                    code=code,
                    defaults={"name_en": name_en, "name_fa": name_fa, "level": 1, "parent": None},
                )
                l1_objs[code] = obj

            for code, (name_en, name_fa) in ATC_L2.items():
                AtcCategory.objects.update_or_create(
                    code=code,
                    defaults={
                        "name_en": name_en,
                        "name_fa": name_fa,
                        "level": 2,
                        "parent": l1_objs.get(code[0]),
                    },
                )

        used_l2 = {
            c[:3] for c in AtcCode.objects.values_list("code", flat=True)
        }
        missing = sorted(used_l2 - set(ATC_L2))
        if missing:
            self.stderr.write(self.style.WARNING(
                "L2 codes in the data with no reference row: " + ", ".join(missing)
            ))

        self.stdout.write(self.style.SUCCESS(
            f"load_atc_reference done: {len(ATC_L1)} L1, {len(ATC_L2)} L2 categories"
        ))
