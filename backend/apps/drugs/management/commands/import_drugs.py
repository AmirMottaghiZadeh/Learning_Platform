import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.drugs.models import Drug, DrugTopic, DrugQuestionSource
from apps.drugs.services import ensure_topics
from apps.drugs.learning_sync import brand_drug_name, generic_drug_name

TOPIC_KEYS = ["timing", "brandGeneric", "indication", "sideEffects"]

def load_window_array(path, var_name):
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(rf"window\.{re.escape(var_name)}\s*=\s*(\[.*?\]);", text, re.S)
    if not match:
        raise CommandError(f"Could not find window.{var_name} in {path}")
    return json.loads(match.group(1))

def text(value):
    return str(value or "").strip()

class Command(BaseCommand):
    help = "Import Pharmexa static JS drug datasets into Django models."

    def add_arguments(self, parser):
        parser.add_argument("--drugs-js", required=True)
        parser.add_argument("--topics-js", required=True)

    def handle(self, *args, **options):
        ensure_topics()
        timing_rows = load_window_array(options["drugs_js"], "DRUGS_DATA")
        topic_rows = load_window_array(options["topics_js"], "DRUG_TOPIC_DATA")
        count = 0

        for row in timing_rows:
            drug, _ = Drug.objects.update_or_create(
                external_id=text(row.get("id")),
                defaults={
                    "name": text(row.get("name")), "persian_name": text(row.get("pname")),
                    "brand_name": text(row.get("brandName")), "dosage_form": text(row.get("dosageForm")),
                    "drug_classification": text(row.get("drugClassification")),
                    "consumption_time": text(row.get("consumptionTime")),
                    "consumption_time_sorted": text(row.get("consumptionTimeSorted")), "raw": row,
                },
            )
            answer = text(row.get("consumptionTimeSorted"))
            if answer in {"با غذا", "بدون غذا", "فرقی نمی‌کند"}:
                topic = DrugTopic.objects.get(key="timing")
                DrugQuestionSource.objects.update_or_create(
                    topic=topic, drug=drug, question_type="timing", correct_answer=answer,
                    defaults={
                        "prompt": f"داروی {generic_drug_name(drug)} چه زمانی نسبت به غذا مصرف می‌شود؟",
                        "subtitle": f"نام فارسی: {drug.persian_name}" if drug.persian_name else "",
                        "chip": drug.dosage_form or "فرم دارویی ثبت نشده",
                        "feedback": drug.consumption_time or f"پاسخ صحیح: {answer}",
                    },
                )
                count += 1

        for row in topic_rows:
            drug, _ = Drug.objects.update_or_create(
                external_id=text(row.get("id")),
                defaults={
                    "brand_name": text(row.get("brandName")), "generic_name": text(row.get("genericName")),
                    "dosage_form": text(row.get("dosageForm")), "drug_classification": text(row.get("drugClassification")),
                    "indication": text(row.get("indication")), "indication_answer": text(row.get("indicationAnswer")),
                    "side_effects": text(row.get("sideEffects")), "side_effects_answer": text(row.get("sideEffectsAnswer")),
                    "source_topic": text(row.get("sourceTopic")), "source_file": text(row.get("sourceFile")), "raw": row,
                },
            )
            if drug.brand_name and drug.generic_name:
                topic = DrugTopic.objects.get(key="brandGeneric")
                DrugQuestionSource.objects.update_or_create(
                    topic=topic, drug=drug, question_type="brandGeneric", correct_answer=drug.generic_name,
                    defaults={
                        "prompt": f"نام ژنریک داروی تجاری {brand_drug_name(drug)} کدام است؟",
                        "subtitle": drug.drug_classification,
                        "chip": drug.drug_classification or "نام تجاری دارو",
                        "feedback": f"{drug.brand_name} = {drug.generic_name}",
                    },
                )
                count += 1
            if drug.indication_answer:
                topic = DrugTopic.objects.get(key="indication")
                DrugQuestionSource.objects.update_or_create(
                    topic=topic, drug=drug, question_type="indication", correct_answer=drug.indication_answer,
                    defaults={
                        "prompt": f"کاربرد اصلی داروی {generic_drug_name(drug)} کدام است؟",
                        "subtitle": f"نام ژنریک: {drug.generic_name}",
                        "chip": drug.drug_classification or "اندیکاسیون",
                        "feedback": f"کاربرد: {drug.indication}",
                    },
                )
                count += 1
            if drug.side_effects_answer:
                topic = DrugTopic.objects.get(key="sideEffects")
                DrugQuestionSource.objects.update_or_create(
                    topic=topic, drug=drug, question_type="sideEffects", correct_answer=drug.side_effects_answer,
                    defaults={
                        "prompt": f"کدام مورد از عوارض جانبی مهم داروی {generic_drug_name(drug)} است؟",
                        "subtitle": f"نام ژنریک: {drug.generic_name}",
                        "chip": drug.drug_classification or "عوارض جانبی",
                        "feedback": f"عوارض مهم: {drug.side_effects}",
                    },
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported/updated {count} question sources."))
