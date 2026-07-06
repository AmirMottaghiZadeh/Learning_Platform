from django.conf import settings

from apps.ai_data_pipeline import constants


class ProviderUnavailableError(RuntimeError):
    pass


class AIProvider:
    provider_name = "base"
    supports_external_calls = False

    def suggest_translation(self, value, *, field_name=""):
        raise NotImplementedError

    def validate_medical_text(self, record):
        raise NotImplementedError


def get_provider(provider_name=None):
    provider_name = provider_name or getattr(settings, "AI_DATA_PIPELINE_PROVIDER", constants.PROVIDER_RULES)
    provider_name = normalize_provider_name(provider_name)
    if provider_name == constants.PROVIDER_RULES:
        from .rules import LocalRulesProvider

        return LocalRulesProvider()
    if provider_name == constants.PROVIDER_MOCK:
        from .mock import LocalMockAIProvider

        return LocalMockAIProvider()
    if provider_name == constants.PROVIDER_OPENAI:
        from .openai import OpenAIProvider

        return OpenAIProvider()
    if provider_name == constants.PROVIDER_OLLAMA:
        from .ollama import OllamaProvider

        return OllamaProvider()
    raise ValueError(f"Unsupported AI data pipeline provider: {provider_name}")


def list_provider_names():
    return [
        constants.PROVIDER_RULES,
        constants.PROVIDER_MOCK,
        constants.PROVIDER_OPENAI,
        constants.PROVIDER_OLLAMA,
    ]


def normalize_provider_name(provider_name):
    return constants.PROVIDER_ALIASES.get(provider_name, provider_name)
