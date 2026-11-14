"""Clinical study-content sections shared by quiz facts and questions."""

# (key, fa label, en label, tone) -- tone is the frontend's SectionTone, so each
# heading is colored like the matching section on the lesson screen.
CARD_SECTIONS = [
    ("indication", "اندیکاسیون", "Indication", "info"),
    ("mechanism", "سازوکار اثر", "Mechanism", "info"),
    ("adr_common", "عوارض شایع", "Common side effects", "caution"),
    ("adr_serious", "عوارض مهم و جدی", "Serious side effects", "deny"),
    ("interaction", "تداخل‌های مهم", "Key interactions", "caution"),
    ("warning", "هشدارهای مهم", "Important warnings", "caution"),
    ("dosage_forms", "اشکال دارویی", "Dosage forms", "special"),
    ("contra_boxed", "منع مطلق و جعبه‌سیاه", "Contraindications & boxed warning", "boxed"),
]

SECTION_KEYS = [key for key, *_ in CARD_SECTIONS]
SECTION_CHOICES = [(key, en) for key, _fa, en, _tone in CARD_SECTIONS]
SECTION_META = {key: {"fa": fa, "en": en, "tone": tone} for key, fa, en, tone in CARD_SECTIONS}
