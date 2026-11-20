"""Bounded question facts and goals, never clinical evidence or a guessed answer.

The existing first search-tool call supplies this profile; understanding a case
does not add another model request. Original questions remain authoritative.
"""
import re

from .provider import ProviderError


KINDS = ("clinical_scenario", "drug_question", "disease_question", "drug_disease",
         "drug_interaction", "comparison", "media_lookup", "general")
OBJECTIVES = ("emergency_care", "diagnosis", "differential", "drug_therapy", "treatment",
              "dose", "renal_dose", "adverse_effects", "contraindications", "interaction",
              "pregnancy", "mechanism", "indications", "monitoring", "comparison",
              "prevention", "general")
SETTINGS = ("general", "prehospital", "emergency", "inpatient", "outpatient")
SECRET = re.compile(r"sk-[A-Za-z0-9_-]{16,}")


def strings(limit, length=100):
    return {"type": "array", "maxItems": limit,
            "items": {"type": "string", "minLength": 1, "maxLength": length}}


SCHEMA = {"type": "object", "description": (
    "On the FIRST search call, classify the WHOLE question and preserve stated case facts. "
    "This is retrieval metadata, NOT a diagnosis or answer. Use concise English terms. "
    "Do not invent diagnoses, positive findings, demographics or clinical values. "
    "Use objectives for what is ASKED, not past treatments mentioned in the history. "
    "Repeat this unchanged or omit it on complementary searches."),
    "properties": {
        "kind": {"type": "string", "enum": list(KINDS)},
        "objectives": {"type": "array", "minItems": 1, "maxItems": 4,
                       "items": {"type": "string", "enum": list(OBJECTIVES)}},
        "focus": {"type": "string", "minLength": 2, "maxLength": 200,
                  "description": "The actual clinical question, preserving critical conditions and negation."},
        "regimen_requested": {"type": "boolean", "description": (
            "True for dosing, general pharmacotherapy/first-line treatment or a requested full therapeutic regimen. "
            "False for a suitability/contraindication/stop-or-continue decision alone, even if changing treatment is mentioned. "
            "A proposed medication is not by itself a request for its dose.")},
        "conditions": {"type": "array", "maxItems": 4, "items": {
            "type": "object", "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "status": {"type": "string", "enum": ["reported", "possible", "excluded"]}},
            "required": ["name", "status"], "additionalProperties": False}},
        "medications": strings(4),
        "findings": {"type": "array", "maxItems": 6, "items": {
            "type": "object", "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "state": {"type": "string", "enum": ["present", "absent", "unknown"]}},
            "required": ["name", "state"], "additionalProperties": False}},
        "constraints": strings(6, 120),
        "care_setting": {"type": "string", "enum": list(SETTINGS)},
    }, "required": ["kind", "objectives", "focus", "regimen_requested"], "additionalProperties": False}


def _text(value, minimum=1, maximum=100):
    if (not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum
            or SECRET.search(value) or any(ord(c) < 32 and c not in "\t\n" for c in value)):
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    return value.strip()


def validate(value):
    """Reject malformed/unbounded model metadata before any source query."""
    if not isinstance(value, dict) or set(value) - set(SCHEMA["properties"]):
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    if value.get("kind") not in KINDS:
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    goals = value.get("objectives")
    if (not isinstance(goals, list) or not 1 <= len(goals) <= 4
            or any(not isinstance(goal, str) or goal not in OBJECTIVES for goal in goals)
            or len(set(goals)) != len(goals)):
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    result = {"kind": value["kind"], "objectives": list(goals),
              "focus": _text(value.get("focus"), 2, 200)}
    regimen = value.get("regimen_requested", goals[0] in {"treatment", "drug_therapy"})
    if type(regimen) is not bool:
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    # General pharmacotherapy/dosing must still include a regimen. A secondary
    # mention of changing therapy in a safety decision must not impose one.
    result["regimen_requested"] = regimen or goals[0] in {"treatment", "drug_therapy"} or bool(
        {"dose", "renal_dose"} & set(goals))
    for field, limit, maximum in [("medications", 4, 100), ("constraints", 6, 120)]:
        rows = value.get(field, [])
        if not isinstance(rows, list) or len(rows) > limit:
            raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
        result[field] = list(dict.fromkeys(_text(row, maximum=maximum) for row in rows))
    for field, limit, state, choices in [
            ("conditions", 4, "status", {"reported", "possible", "excluded"}),
            ("findings", 6, "state", {"present", "absent", "unknown"})]:
        rows = value.get(field, [])
        if not isinstance(rows, list) or len(rows) > limit:
            raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
        result[field] = []
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {"name", state}
                    or not isinstance(row.get(state), str) or row[state] not in choices):
                raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
            result[field].append({"name": _text(row["name"]), state: row[state]})
    setting = value.get("care_setting", "general")
    if not isinstance(setting, str) or setting not in SETTINGS:
        raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
    result["care_setting"] = setting
    return result


def entities(profile):
    """Only named entities; absent findings/excluded diagnoses are not positives."""
    conditions = [row["name"] for row in profile.get("conditions", []) if row["status"] != "excluded"]
    medications = profile.get("medications", [])
    ordered = medications + conditions if profile.get("kind") == "drug_question" else conditions + medications
    return list(dict.fromkeys(ordered))


def keywords(profile, original=()):
    # A broad case must not lose its distinguishing finding to generic query
    # hints. Unknown/absent facts stay in the full model/verification profile.
    important = [row["name"] for row in profile["findings"] if row["state"] == "present"]
    return list(dict.fromkeys([*important, *profile["constraints"], *original]))[:8]


def requirements(profile):
    goals = set(profile["objectives"])
    result = ["requested_aspects"]
    if profile["kind"] == "clinical_scenario":
        result.append("case_applicability")
    if goals & {"diagnosis", "differential"}:
        result.append("diagnostic_assessment")
    if "emergency_care" in goals:
        result.append("immediate_actions")
    if "contraindications" in goals:
        result.append("intervention_safety")
    if profile["kind"] in {"drug_disease", "drug_interaction"} or "interaction" in goals:
        result.append("entity_relationship")
    if goals & {"treatment", "drug_therapy"}:
        result.append("treatment_selection")
    if profile["regimen_requested"]:
        result.append("drug_regimen")
    if profile["regimen_requested"] or goals & {"treatment", "drug_therapy"}:
        result.append("important_restrictions")
    return result


def question_parts(question):
    # A vignette's sentences, lists and final question belong together. The
    # model can cover several requested aspects without losing the case facts
    # or making another planning call for each newline/question mark.
    return [question.strip().rstrip("؟?؛; \n")]
