import Engine from "./engine";
import type { DoseRange, PatientInput, PediatricDraft, PediatricDrug, RegimenDefinition, RegimenResult } from "./types";
import { parseTypedNumber } from "@/utils/typedNumber";

export function emptyDraft(): PediatricDraft {
  return { step: 1, age: "", ageUnit: "year", weight: "", ga: "", drugId: "", regimenId: "", productId: "", frequency: "" };
}

export function patientInput(draft: PediatricDraft): PatientInput {
  return {
    ageValue: parseTypedNumber(draft.age), ageUnit: draft.ageUnit, weightKg: parseTypedNumber(draft.weight),
    gaWeeks: draft.ga.trim() ? parseTypedNumber(draft.ga) : undefined,
  };
}

/** Use the upstream validator without assuming any drug or gestational age. */
export function validatePatient(draft: PediatricDraft) {
  const neutral: PediatricDrug = { id: "patient", name: "", source: { title: "", contentId: "" }, products: {}, regimens: [] };
  return Engine.calculate(neutral, patientInput(draft));
}

export function needsFrequency(regimen: RegimenDefinition | undefined, result: RegimenResult | undefined) {
  return !!regimen && !regimen.stages && !regimen.components && (result?.results.length ?? 0) > 1;
}

/** Staged regimens retain every source stage. Combination outputs are already
 * separated by preparation by the upstream engine. Never merge their doses. */
export function selectedResults(raw: RegimenDefinition | undefined, regimen: RegimenResult | undefined, draft: PediatricDraft) {
  if (!regimen || !raw) return [];
  return regimen.results.filter(result =>
    result.products.some(product => product.productId === draft.productId) &&
    (!needsFrequency(raw, regimen) || result.freq === draft.frequency),
  );
}

export function formatDoseRange(value: DoseRange | undefined, isFa: boolean): string {
  if (!value) return "—";
  const fmt = (number: number) => Number(number.toPrecision(8)).toLocaleString(isFa ? "fa-IR" : "en-US", { maximumSignificantDigits: 8, useGrouping: false });
  return value[0] === value[1] ? fmt(value[0]) : `${fmt(value[0])}–${fmt(value[1])}`;
}

const ENGLISH_ERRORS: Record<string, string> = {
  "وزن نامعتبر است": "Enter a valid weight.", "سن نامعتبر است": "Enter a valid age.",
  "وزن بیش از ۲۰۰ کیلوگرم است": "Weight must not exceed 200 kg.",
  "واحد سن نامعتبر است": "Select a valid age unit.",
  "این ماشین‌حساب فقط برای سن زیر ۱۹ سال است": "This calculator is for ages under 19 years.",
  "سن حاملگی باید عددی بین ۲۲ تا ۴۴ هفته باشد": "Gestational age must be between 22 and 44 weeks.",
  "برای محاسبهٔ این دارو، سن حاملگی هنگام تولد را وارد کنید": "Enter gestational age at birth for this drug.",
};
export function errorText(message: string, isFa: boolean) { return isFa ? message : ENGLISH_ERRORS[message] || message; }
