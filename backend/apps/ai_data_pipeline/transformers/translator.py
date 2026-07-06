from .normalizer import has_persian, normalize_text
from .terminology_checker import load_terminology_map


class LocalMedicalTranslator:
    provider_name = "rules"

    def translate_to_english(self, value, *, field_name=""):
        text = normalize_text(value)
        if not text or not has_persian(text):
            return None

        translations = load_terminology_map().get("english_translations", {})
        translated = translations.get(text)
        confidence = 0.9 if translated else 0.35
        if not translated:
            for persian, english in translations.items():
                if persian in text:
                    text = text.replace(persian, english)
                    translated = text
            if not translated:
                return {
                    "translated_value": "",
                    "reason": "Persian medical text detected, but the local rules map has no safe English match. Manual review/edit required.",
                    "confidence_score": confidence,
                    "risk_level": "needs_review",
                    "metadata": {"field_name": field_name, "requires_manual_review": True},
                }

        return {
            "translated_value": translated,
            "reason": "Rule-based medical terminology translation suggestion. Original Persian text remains unchanged.",
            "confidence_score": confidence,
            "risk_level": "needs_review" if confidence < 0.85 else "safe",
            "metadata": {"field_name": field_name, "requires_manual_review": confidence < 0.85},
        }
