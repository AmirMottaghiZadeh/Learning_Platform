BATCH_TYPE_HEALTH_CHECK = "health_check"
BATCH_TYPE_SUGGESTION_GENERATION = "suggestion_generation"
BATCH_TYPE_APPLY = "apply"
BATCH_TYPE_REPORT = "report"

BATCH_STATUS_CREATED = "created"
BATCH_STATUS_RUNNING = "running"
BATCH_STATUS_COMPLETED = "completed"
BATCH_STATUS_FAILED = "failed"

JOB_TYPE_HEALTH_CHECK = "health_check"
JOB_TYPE_NORMALIZATION = "normalization"
JOB_TYPE_TERMINOLOGY_CHECK = "terminology_check"
JOB_TYPE_DUPLICATE_DETECTION = "duplicate_detection"
JOB_TYPE_MEDICAL_VALIDATION = "medical_validation"
JOB_TYPE_TRANSLATION = "translation"
JOB_TYPE_FULL_RULES_REVIEW = "full_rules_review"

JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

PROVIDER_RULES = "rules"
PROVIDER_MOCK = "mock"
PROVIDER_OPENAI = "openai"
PROVIDER_OLLAMA = "ollama"
PROVIDER_MANUAL = "manual"
PROVIDER_CHOICES = {
    PROVIDER_RULES,
    PROVIDER_MOCK,
    PROVIDER_OPENAI,
    PROVIDER_OLLAMA,
    PROVIDER_MANUAL,
}
PROVIDER_ALIASES = {
    "local-rules": PROVIDER_RULES,
    "local-mock": PROVIDER_MOCK,
}

SUGGESTION_STATUS_PENDING = "pending"
SUGGESTION_STATUS_APPROVED = "approved"
SUGGESTION_STATUS_REJECTED = "rejected"
SUGGESTION_STATUS_EDITED = "edited"
SUGGESTION_STATUS_APPLIED = "applied"
SUGGESTION_STATUS_FAILED = "failed"

RISK_SAFE = "safe"
RISK_NEEDS_REVIEW = "needs_review"
RISK_RISKY = "risky"

SUGGESTION_TYPE_NORMALIZATION = "normalization"
SUGGESTION_TYPE_STANDARDIZATION = "standardization"
SUGGESTION_TYPE_TRANSLATION = "translation"
SUGGESTION_TYPE_DUPLICATE = "duplicate"
SUGGESTION_TYPE_MERGE = "merge"
SUGGESTION_TYPE_DELETE_RECOMMENDATION = "delete_recommendation"
SUGGESTION_TYPE_MEDICAL_WARNING = "medical_warning"
SUGGESTION_TYPE_TERMINOLOGY = "terminology"

APPLYABLE_SUGGESTION_TYPES = {
    SUGGESTION_TYPE_NORMALIZATION,
    SUGGESTION_TYPE_STANDARDIZATION,
    SUGGESTION_TYPE_TRANSLATION,
    SUGGESTION_TYPE_TERMINOLOGY,
}

DRUG_TABLE = "drugs_drug"
DRUG_QUESTION_SOURCE_TABLE = "drugs_drugquestionsource"
TRANSLATION_TABLE = "ai_data_pipeline_translation"

ALLOWED_APPLY_FIELDS = {
    DRUG_TABLE: {
        "name",
        "persian_name",
        "brand_name",
        "generic_name",
        "dosage_form",
        "drug_classification",
        "consumption_time",
        "consumption_time_sorted",
        "indication",
        "indication_answer",
        "side_effects",
        "side_effects_answer",
        "source_topic",
        "source_file",
    },
    DRUG_QUESTION_SOURCE_TABLE: {
        "prompt",
        "subtitle",
        "chip",
        "correct_answer",
        "feedback",
    },
}

ALLOWED_REVIEW_TABLES = {
    *ALLOWED_APPLY_FIELDS.keys(),
    TRANSLATION_TABLE,
}

DRUG_TEXT_FIELDS = [
    "name",
    "persian_name",
    "brand_name",
    "generic_name",
    "dosage_form",
    "drug_classification",
    "consumption_time",
    "consumption_time_sorted",
    "indication",
    "indication_answer",
    "side_effects",
    "side_effects_answer",
    "source_topic",
    "source_file",
]

IMPORTANT_DRUG_FIELDS = [
    "name",
    "persian_name",
    "brand_name",
    "generic_name",
    "dosage_form",
    "drug_classification",
]

TRANSLATABLE_FIELDS = [
    "persian_name",
    "indication",
    "indication_answer",
    "side_effects",
    "side_effects_answer",
    "drug_classification",
]
