from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetCategory:
    key: str
    label: str
    source_values: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


TARGET_CATEGORIES: tuple[TargetCategory, ...] = (
    TargetCategory(
        key="cardiovascular",
        label="قلب و عروق / چربی خون",
        source_values=("cardiovascular + dyslipidemia",),
        keywords=(
            "cardio",
            "dyslipidemia",
            "diuretic",
            "blocker",
            "channel blocker",
            "ccb",
            "antiarrhyth",
            "اریتمی",
            "کلسترول",
            "statin",
            "fibrate",
            "nitrate",
            "antiplatelet",
            "anticoagulant",
            "thrombo",
            "heparin",
            "warfarin",
            "sartan",
            "alpha-blocker",
            "beta-blocker",
        ),
    ),
    TargetCategory(
        key="cns",
        label="CNS / اعصاب و روان",
        source_values=("cns-1", "cns-2", "sedative"),
        keywords=(
            "cns",
            "ssri",
            "snri",
            "tca",
            "maoi",
            "antidepress",
            "antipsychotic",
            "benzodiazep",
            "sedative",
            "hypnotic",
            "anticonvuls",
            "dopamine",
            "پارکینسون",
            "ضد تشنج",
            "اپیوئید",
            "opioid",
        ),
    ),
    TargetCategory(
        key="respiratory",
        label="تنفسی / آلرژی",
        source_values=("respiratory",),
        keywords=(
            "respiratory",
            "تنفسی",
            "antihistamine",
            "هیستامین",
            "decongestant",
            "bronchodilator",
            "leukotriene",
            "asthma",
            "copd",
            "ics",
            "استنشاقی",
        ),
    ),
    TargetCategory(
        key="endocrine",
        label="غدد / دیابت",
        source_values=("endo",),
        keywords=(
            "endo",
            "diabetes",
            "دیابت",
            "insulin",
            "thyroid",
            "تیروئید",
            "glucocorticoid",
            "corticosteroid",
        ),
    ),
    TargetCategory(
        key="gi",
        label="گوارش",
        source_values=("gi",),
        keywords=(
            "gi",
            "gastro",
            "ppi",
            "proton pump",
            "antacid",
            "laxative",
            "antiemetic",
            "ضد اسپاسم",
            "گوارش",
        ),
    ),
    TargetCategory(
        key="infection",
        label="عفونت",
        source_values=("infection",),
        keywords=(
            "infection",
            "penicillin",
            "پنی سیلین",
            "cephalosporin",
            "سفالوسپورین",
            "macrolide",
            "ماکرولید",
            "quinolone",
            "فلورو",
            "antibiotic",
            "antiviral",
            "antifungal",
            "azole",
            "ایمیدازول",
            "hcv",
            "hiv",
            "nrtis",
            "ضد کرم",
        ),
    ),
    TargetCategory(
        key="pain_inflammation",
        label="درد / التهاب",
        source_values=("pain_inflammation",),
        keywords=(
            "nsaid",
            "pain",
            "analgesic",
            "مسکن",
            "التهاب",
            "migraine",
        ),
    ),
    TargetCategory(
        key="urology",
        label="اورولوژی",
        keywords=(
            "pde5",
            "sildenafil",
            "tadalafil",
            "bph",
            "prostate",
            "پروستات",
            "urinary",
            "urolog",
        ),
    ),
    TargetCategory(key="other", label="سایر"),
)

TARGET_CATEGORY_BY_KEY = {category.key: category for category in TARGET_CATEGORIES}


def normalize_category_text(value: str | None) -> str:
    normalized = " ".join(str(value or "").replace(".docx", "").split()).strip()
    return normalized.replace("ي", "ی").replace("ك", "ک").lower()


def category_for_values(
    *,
    source_topic: str = "",
    source_file: str = "",
    drug_classification: str = "",
) -> TargetCategory:
    source_value = normalize_category_text(source_topic) or normalize_category_text(source_file)
    if source_value:
        for category in TARGET_CATEGORIES:
            if source_value in category.source_values:
                return category

    classification = normalize_category_text(drug_classification)
    if classification:
        for category in TARGET_CATEGORIES:
            if any(keyword in classification for keyword in category.keywords):
                return category

    return TARGET_CATEGORY_BY_KEY["other"]


def category_for_drug(drug) -> TargetCategory:
    return category_for_values(
        source_topic=getattr(drug, "source_topic", ""),
        source_file=getattr(drug, "source_file", ""),
        drug_classification=(
            getattr(drug, "drug_classification", "")
            or " ".join(getattr(drug, "category", []) or [])
            or " ".join(getattr(drug, "atc_categories", []) or [])
        ),
    )


def category_payload_for_drug(drug) -> dict[str, str]:
    category = category_for_drug(drug)
    source = (
        getattr(drug, "source_topic", "")
        or getattr(drug, "source_file", "")
        or getattr(drug, "drug_classification", "")
    )
    return {
        "target_category_key": category.key,
        "target_category_label": category.label,
        "target_category_source": source,
    }
