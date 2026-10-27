import type { CalculatorChoice } from "../api/types";
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
