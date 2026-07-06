from .base import AIProvider, ProviderUnavailableError


class OllamaProvider(AIProvider):
    provider_name = "ollama"
    supports_external_calls = True

    def suggest_translation(self, value, *, field_name=""):
        raise ProviderUnavailableError("Ollama provider is a placeholder and is disabled in the current no-external-API mode.")

    def validate_medical_text(self, record):
        raise ProviderUnavailableError("Ollama provider is a placeholder and is disabled in the current no-external-API mode.")
