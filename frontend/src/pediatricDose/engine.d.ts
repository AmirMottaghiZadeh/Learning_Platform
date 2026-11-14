import { AgeUnit, Calculation, PatientInput, PediatricDrug, Population } from "./types";

declare const engine: {
  calculate(drug: PediatricDrug, input: PatientInput): Calculation;
  ageToDays(value: number, unit: AgeUnit): number;
  parseAge(value: string): number;
  matchPop(pop: Population, context: { ageDays: number; weightKg?: number; gaWeeks?: number | null }): boolean;
  needsGA(drug: PediatricDrug, ageDays: number | null): boolean;
};
export = engine;
