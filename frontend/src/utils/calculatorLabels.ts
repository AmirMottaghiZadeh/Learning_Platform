import type { CalculatorChoice, CalculatorQuestion } from "../api/types";
import { stripHtml } from "./html";

/** Display only: the original factors, thresholds and formulas stay intact. */
export function calculatorLabel(raw: string, isFa: boolean): string {
  const words = isFa
    ? { "<": "کمتر از", ">": "بیشتر از", "≤": "کمتر یا مساوی", "≥": "بیشتر یا مساوی" }
    : { "<": "less than", ">": "greater than", "≤": "less than or equal to", "≥": "greater than or equal to" };
  return stripHtml(raw)
    .replace(/<=/g, "≤")
    .replace(/>=/g, "≥")
    .replace(/[<>≤≥]/g, (symbol) => ` ${words[symbol as keyof typeof words]} `)
    .replace(/([\d۰-۹٠-٩])\s*[-–]\s*(?=[\d۰-۹٠-٩])/g, `$1 ${isFa ? "تا" : "to"} `)
    .replace(/\s+/g, " ")
    .trim();
}

/** Secondary labels contain the source's alternate units (and sometimes a
 * clinical explanation). Use each translated field independently, with an
 * English fallback, and never invent a conversion or repeat identical text. */
export function choiceLabels(choice: CalculatorChoice, isFa: boolean): string[] {
  const primary = calculatorLabel(isFa && choice.title_primary_fa ? choice.title_primary_fa : choice.title_primary, isFa);
  const secondary = calculatorLabel((isFa && choice.title_secondary_fa ? choice.title_secondary_fa : choice.title_secondary) ?? "", isFa);
  return [...new Set([primary, secondary].filter(Boolean))];
}

export type UnitSystem = "si" | "us";

// A unit counts only right after a number, so the word "in" or "m" in a
// sentence is not read as inches or metres.
const UNIT = /\d\s*((?:[µμu]?mol|mmol|nmol|pmol|mg|g|meq)\s*\/\s*(?:dl|l)\b|°\s*[cf]\b|kpa\b|mmhg\b|cm\b|kg\b|lbs?\b|inch(?:es)?\b|in\b|meters?\b|miles?\b)/gi;
const SYSTEM_OF: Record<string, UnitSystem> = {
  "mol/l": "si", "µmol/l": "si", "μmol/l": "si", "umol/l": "si", "mmol/l": "si", "nmol/l": "si", "pmol/l": "si",
  "g/l": "si", "°c": "si", kpa: "si", cm: "si", kg: "si", meter: "si", meters: "si",
  "mg/dl": "us", "g/dl": "us", "meq/l": "us", "°f": "us", mmhg: "us", lb: "us", lbs: "us",
  in: "us", inch: "us", inches: "us", mile: "us", miles: "us",
};

function unitsOf(text: string): Set<string> {
  return new Set([...stripHtml(text).matchAll(UNIT)].map((m) => m[1].toLowerCase().replace(/\s+/g, "")));
}

function systemOf(units: Set<string>): UnitSystem | null {
  const systems = [...units].map((u) => SYSTEM_OF[u]);
  return systems.length && systems.every((s) => s && s === systems[0]) ? systems[0] : null;
}

/** Which unit system each of a choice's two labels is written in, when they
 * are the same range in SI and US units («34–50 µmol/L» / «2.0–3.0 mg/dL»).
 * Read from the English fields; units both labels share are ignored. Null
 * for anything else: an explanation, a pair in one system (ng/mL / µg/mL),
 * a label with no unit. */
export function choiceUnitPair(choice: CalculatorChoice): { primary: UnitSystem; secondary: UnitSystem } | null {
  const a = unitsOf(choice.title_primary ?? "");
  const b = unitsOf(choice.title_secondary ?? "");
  const primary = systemOf(new Set([...a].filter((u) => !b.has(u))));
  const secondary = systemOf(new Set([...b].filter((u) => !a.has(u))));
  return primary && secondary && primary !== secondary ? { primary, secondary } : null;
}

/** What a choice shows: with a unit system picked, only the label in that
 * system; otherwise the first label in full and the second one under it. */
export function choiceDisplay(choice: CalculatorChoice, isFa: boolean, system: UnitSystem | null): { main: string; sub: string | null } {
  const labels = choiceLabels(choice, isFa);
  const pair = system && labels.length === 2 ? choiceUnitPair(choice) : null;
  if (pair) return { main: pair.primary === system ? labels[0] : labels[1], sub: null };
  return { main: labels[0] ?? "", sub: labels[1] ?? null };
}

/** The calculator's choice labels that come in both SI and US units: whether
 * there are any, the system most of their first labels use (the source's
 * default), and up to two units of each system to name the switch by. */
export function choiceUnitSystems(questions: CalculatorQuestion[]): { default: UnitSystem; units: Record<UnitSystem, string[]> } | null {
  const count: Record<UnitSystem, number> = { si: 0, us: 0 };
  const units: Record<UnitSystem, string[]> = { si: [], us: [] };
  for (const q of questions) {
    if (q.type !== "multiple_choice") continue;
    for (const c of q.choices) {
      const pair = choiceUnitPair(c);
      if (!pair) continue;
      count[pair.primary] += 1;
      for (const [text, system] of [[c.title_primary, pair.primary], [c.title_secondary ?? "", pair.secondary]] as const) {
        for (const m of stripHtml(text).matchAll(UNIT)) {
          const unit = m[1].replace(/\s+/g, "");
          if (SYSTEM_OF[unit.toLowerCase()] === system && !units[system].some((u) => u.toLowerCase() === unit.toLowerCase())) {
            units[system].push(unit);
          }
        }
      }
    }
  }
  if (!count.si && !count.us) return null;
  return { default: count.us > count.si ? "us" : "si", units: { si: units.si.slice(0, 2), us: units.us.slice(0, 2) } };
}
