export type AgeUnit = "day" | "month" | "year";
export type DoseRange = [number, number];
export type Source = { title: string; contentId: string };
export type Population = Record<string, string | number> | Population[];

export interface Preparation {
  label: string;
  mgOnly?: boolean;
  doseUnit?: string;
  verificationStatus?: string;
  [key: string]: unknown;
}

export interface RegimenDefinition {
  id: string;
  indication: string;
  population: string;
  pop: Population;
  products: string[];
  stages?: unknown[];
  components?: unknown[];
  [key: string]: unknown;
}

export interface PediatricDrug {
  id: string;
  name: string;
  source: Source;
  products: Record<string, Preparation>;
  regimens: RegimenDefinition[];
  gaAgeLt?: string;
  [key: string]: unknown;
}

export interface PediatricDataset {
  schema_version: number;
  engine_sha256: string;
  source: string;
  drugs: PediatricDrug[];
}

export interface PatientInput {
  ageValue: number;
  ageUnit: AgeUnit;
  weightKg: number;
  gaWeeks?: number | null;
}

export interface ProductResult {
  productId: string;
  product: string;
  ok: boolean;
  reason?: string;
  amount?: DoseRange;
  unit?: string;
  mg?: DoseRange;
  mgOnly?: boolean;
  amountText: string;
  dailyMaxText?: string;
  components?: { name: string; mgAtVolume: DoseRange }[];
}

export interface DoseResult {
  stage: string | null;
  freq: string;
  freqFa: string;
  freqEn: string;
  order: string;
  mgPerDose?: DoseRange;
  mgPerDay?: DoseRange;
  unit?: string;
  capped: string[];
  dailyMax?: number | null;
  maxDosesPerDay?: number;
  maxDosesAtHigh?: number;
  schedule?: { fa: string; en: string };
  products: ProductResult[];
  combo?: boolean;
}

export interface RegimenResult {
  id: string;
  indication: string;
  population: string;
  route: string;
  duration: string | null;
  limitedData: boolean;
  notes: string[];
  warnings: string[];
  source: Source;
  quotes: string[];
  results: DoseResult[];
}

export interface Calculation {
  errors: string[];
  ctx?: { ageDays: number; weightKg: number; gaWeeks: number | null };
  regimens: RegimenResult[];
  messages: string[];
  drugNotes?: string[];
}

/** Screen-local state; never persisted or sent to the API. */
export interface PediatricDraft {
  step: 1 | 2 | 3;
  age: string;
  ageUnit: AgeUnit;
  weight: string;
  ga: string;
  drugId: string;
  regimenId: string;
  productId: string;
  frequency: string;
}
