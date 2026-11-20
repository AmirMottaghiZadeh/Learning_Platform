"""Load the bundled bilingual ATC L1/L2 reference into drugs.AtcCategory.

Idempotent (matched on `code`). Warns about any L2 code that appears in the
imported ingredient data but has no reference row, and about reference rows for
L2 codes that no ingredient uses (harmless, just unused).

This runs on every boot via release.sh -- including a free-tier host waking
back up from an idle sleep, not just a real deploy. The reference set is
static WHO ATC data that essentially never changes once loaded, so the
expensive part (an update_or_create per code, ~200 queries total) is skipped
whenever every code is already present; pass --force to bypass that and
re-sync everything (e.g. after actually editing atc_reference.py's names).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.drugs.data.atc_reference import ATC_L1, ATC_L2
from apps.drugs.models import AtcCategory, AtcCode


class Command(BaseCommand):
    help = "Load the ATC L1/L2 category reference."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-sync every row even if the full reference set is already "
            "present (use after editing atc_reference.py's names/parents).",
        )

    def handle(self, *args, **options):
        expected_codes = set(ATC_L1) | set(ATC_L2)
        existing_codes = set(
            AtcCategory.objects.filter(code__in=expected_codes).values_list("code", flat=True)
        )
        already_loaded = not options["force"] and existing_codes == expected_codes

        if already_loaded:
            self.stdout.write(self.style.SUCCESS(
                f"load_atc_reference: {len(ATC_L1)} L1, {len(ATC_L2)} L2 categories "
                "already loaded, skipping."
            ))
        else:
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

            self.stdout.write(self.style.SUCCESS(
                f"load_atc_reference done: {len(ATC_L1)} L1, {len(ATC_L2)} L2 categories"
            ))

        used_l2 = {
            c[:3] for c in AtcCode.objects.values_list("code", flat=True)
        }
        missing = sorted(used_l2 - set(ATC_L2))
        if missing:
            self.stderr.write(self.style.WARNING(
                "L2 codes in the data with no reference row: " + ", ".join(missing)
            ))
