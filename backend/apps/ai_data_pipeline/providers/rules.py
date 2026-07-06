from apps.ai_data_pipeline.transformers.translator import LocalMedicalTranslator

from .base import AIProvider


class LocalRulesProvider(AIProvider):
    provider_name = "rules"

    def __init__(self):
        self.translator = LocalMedicalTranslator()

    def suggest_translation(self, value, *, field_name=""):
        return self.translator.translate_to_english(value, field_name=field_name)

    def validate_medical_text(self, record):
        return []
