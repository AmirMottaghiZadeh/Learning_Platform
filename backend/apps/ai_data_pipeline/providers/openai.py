from .base import AIProvider, ProviderUnavailableError


class OpenAIProvider(AIProvider):
    provider_name = "openai"
    supports_external_calls = True

    def suggest_translation(self, value, *, field_name=""):
        raise ProviderUnavailableError("OpenAI provider is a placeholder and is disabled in the current no-external-API mode.")

    def validate_medical_text(self, record):
        raise ProviderUnavailableError("OpenAI provider is a placeholder and is disabled in the current no-external-API mode.")
