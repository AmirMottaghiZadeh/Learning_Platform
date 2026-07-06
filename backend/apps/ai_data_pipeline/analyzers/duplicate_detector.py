from difflib import SequenceMatcher
from collections import defaultdict

from apps.drugs.models import Drug
from apps.drugs.services import generic_drug_signature

from apps.ai_data_pipeline.transformers.normalizer import canonical_signature, normalize_text


def drug_identity_signature(drug):
    generic = generic_drug_signature(drug)
    brand = canonical_signature(drug.brand_name)
    dosage = canonical_signature(drug.dosage_form)
    return "|".join([generic, brand, dosage]).strip("|")


def detect_exact_duplicates(queryset=None):
    queryset = queryset or Drug.objects.all()
    buckets = defaultdict(list)
    for drug in queryset:
        signature = drug_identity_signature(drug)
        if signature:
            buckets[signature].append(drug)
    duplicates = []
    for signature, records in buckets.items():
        if len(records) > 1:
            duplicates.append({
                "signature": signature,
                "record_ids": [record.id for record in records],
                "external_ids": [record.external_id for record in records],
                "kind": "exact",
            })
    return duplicates


def _display_value(drug):
    return normalize_text(drug.generic_name or drug.name or drug.persian_name or drug.brand_name)


def detect_near_duplicates(queryset=None, threshold=0.92, max_pairs=250):
    queryset = list(queryset or Drug.objects.all())
    candidates = []
    values = [(drug, _display_value(drug)) for drug in queryset]
    for index, (left, left_value) in enumerate(values):
        if not left_value:
            continue
        for right, right_value in values[index + 1:]:
            if not right_value:
                continue
            ratio = SequenceMatcher(None, left_value.casefold(), right_value.casefold()).ratio()
            if ratio >= threshold and left.id != right.id:
                candidates.append({
                    "left_id": left.id,
                    "right_id": right.id,
                    "left_external_id": left.external_id,
                    "right_external_id": right.external_id,
                    "left_value": left_value,
                    "right_value": right_value,
                    "score": round(ratio, 3),
                    "kind": "near",
                })
                if len(candidates) >= max_pairs:
                    return candidates
    return candidates
