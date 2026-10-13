"""Persian names for what the console shows: clinical fields and the state
of each section in the workspace's section list."""

from apps.drugs.serializers import LESSON_SECTION_MAP

# Same names the app's lesson pages use for these sections.
FIELD_FA = {field: fa for _key, field, fa, _en, _tone in LESSON_SECTION_MAP}
FIELD_FA.setdefault("clinical_pharmacology", "فارماکولوژی بالینی")

# key -> (label, tone); tone picks the chip colour in base.html.
STATES = {
    "pending": ("در انتظار تأیید", "warn"),
    "changes": ("نیاز به اصلاح", "orange"),
    "locked": ("در دست دیگری", "muted"),
    "draft": ("پیش‌نویس", "teal"),
    "missing": ("بدون خلاصه", "danger"),
    "approved": ("تأییدشده", "ok"),
    "unreviewed": ("بازبینی‌نشده", "muted"),
    "no_source": ("بدون متن منبع", "muted"),
}


def section_state(section, open_request, has_my_draft, has_applied_edit, user):
    """The one state a section shows in the list, most actionable first."""
    if open_request is not None:
        if open_request.requested_by_id != user.id:
            key = "locked"
        else:
            key = "pending" if open_request.is_pending else "changes"
    elif has_my_draft:
        key = "draft"
    elif section.raw_text and (not section.summary_fa or not section.summary_en):
        key = "missing"
    elif has_applied_edit:
        key = "approved"
    elif section.summary_fa or section.summary_en:
        key = "unreviewed"
    else:
        key = "no_source"
    label, tone = STATES[key]
    return {"key": key, "label": label, "tone": tone}
