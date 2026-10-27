/**
 * Which kind of result a calculator produces, so the result screen can use
 * the layout that suits it (a tier bar for a clinical score, a ring for a
 * risk, a yes/no badge for a verdict, ...).
 *
 * A calculator's output only exists once its formulas run, and the formulas
 * are the source data's own, so the kind is read from what the calculator
 * actually answers: it is run on a fixed, seeded set of sample answers and
 * the shape of what comes back (a whole-number score, a percentage, a value
 * with a unit, a label, a paragraph, ...) decides the model. The same
 * calculator therefore always gets the same model, and the result is cached.
 */

import { CalculatorDetail, CalculatorQuestion, CalculatorResultDef } from "@/api/types";

import { CalculatorAnswers, ComputedResult, computeCalculator, unitFactorOf } from "./calculatorEngine";
import { htmlToParagraphs } from "./html";

export type ResultModel =
  | "score"
  | "risk"
  | "index"
  | "measure"
  | "verdict"
  | "narrative"
  | "panel"
  | "dose"
  | "staging"
  | "date"
  | "plain";

/** yes/no badge, a ladder of categories, or a decision (an action to take). */
export type VerdictStyle = "yesno" | "ladder" | "decision";
export type NarrativeStyle = "headline" | "sections";

export interface LadderRung {
  en: string;
  fa: string;
}

export interface ModelInfo {
  model: ResultModel;
  verdict?: VerdictStyle;
  narrative?: NarrativeStyle;
  /** Every category a ladder verdict can land on, lowest first. */
  ladder?: LadderRung[];
}

/** A result row with a blank `answer` is a helper the source formulas read
 * ($result0 feeding a later row) and shows nothing of its own. */
export function isDisplayedResult(def: Pick<CalculatorResultDef, "answer">): boolean {
  return (def.answer ?? "").trim() !== "";
}

export type ValueKind = "empty" | "num" | "pct" | "numunit" | "stage" | "tnm" | "text" | "mixed" | "label" | "date" | "age";

const NUM = /^[<>≤≥~]?\s*-?\d+(\.\d+)?\s*$/;
const PCT = /^[<>≤≥~]?\s*-?\d+(\.\d+)?(\s*-\s*\d+(\.\d+)?)?\s*%$/;
const NUMUNIT = /^[<>≤≥~]?\s*-?\d+(\.\d+)?\s*[A-Za-zµμ°][\w/.²³·^*\u207B\u2070-\u2079 ]{0,25}$/;
const STAGE = /^(p|c|y)?[TNMG][0-4XxIiSs]\w{0,3}$/;
const DATE = /^[A-Z][a-z]{2,8},?\s+\d{1,2},?\s+\d{4}$|^[A-Z][a-z]{2,8},?\s+\d{4}$/;
const AGE = /^\d+\s*weeks?[\s,]*(\d+\s*days?)?$/i;

/** A result's text with its markup removed and line breaks kept. */
export function resultText(raw: string | null | undefined): string {
  return htmlToParagraphs(raw ?? "").replace(/[ \t]+/g, " ").trim();
}

export function valueKind(raw: string | null | undefined): ValueKind {
  const o = resultText(raw);
  if (!o) return "empty";
  if (NUM.test(o)) return "num";
  if (PCT.test(o)) return "pct";
  if (DATE.test(o)) return "date";
  if (AGE.test(o.replace(/\n/g, " "))) return "age";
  if (NUMUNIT.test(o)) return "numunit";
  if (tnmTokens(o)) return "tnm";
  if (STAGE.test(o)) return "stage";
  const first = o.split("\n")[0].trim();
  if (/^[<>≤≥~]?\s*-?\d+(\.\d+)?\s*%\s*\(/.test(first) && o.length < 60) return "pct";
  if (
    /^[<>≤≥~]?\s*-?\d+(\.\d+)?\s*[A-Za-zµμ°][\w/.²³·^*\u207B\u2070-\u2079 ]{0,14}\s*\([^)]*\d[^)]*\)\s*$/.test(o.replace(/\n/g, "")) &&
    o.length < 70
  ) {
    return "numunit";
  }
  if (o.length > 70 || o.includes("•") || o.includes("\n")) return "text";
  if (/^-?\d+(\.\d+)?\s*\(/.test(o)) return "num";
  if (/\d/.test(o)) return "mixed";
  return "label";
}

/** "T2 N1 M0" (or "pT2a cN1 M1a"): the T, N and M codes of one TNM classification. */
export function tnmTokens(text: string): { axis: "T" | "N" | "M"; code: string }[] | null {
  const parts = resultText(text).split(/\s+/).filter(Boolean);
  if (parts.length < 2 || parts.length > 4) return null;
  const out: { axis: "T" | "N" | "M"; code: string }[] = [];
  for (const part of parts) {
    const axis = tnmAxis(part);
    if (!axis) return null;
    out.push({ axis, code: part });
  }
  return out;
}

const isNumeric = (k: ValueKind) => k === "num" || k === "pct" || k === "numunit";

// ---- sampling -----------------------------------------------------------

const SAMPLES = 25;
const DAY_MS = 86_400_000;

function makeRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

const num = (v: string | null | undefined) => {
  if (v === null || v === undefined || v === "") return NaN;
  return parseFloat(v);
};

function sampleAnswers(questions: CalculatorQuestion[], middle: boolean, rnd: () => number): CalculatorAnswers {
  const a: CalculatorAnswers = {};
  for (const q of questions) {
    if (q.type === "multiple_choice") {
      const factors = q.choices.map((c) => num(c.answer_factor)).filter((v) => !Number.isNaN(v));
      if (factors.length) a[q.position] = middle ? factors[Math.floor(factors.length / 2)] : factors[Math.floor(rnd() * factors.length)];
    } else if (q.type === "date_input") {
      a[q.position] = Date.now() - Math.floor(rnd() * 200) * DAY_MS;
    } else if (q.type === "days_input") {
      a[q.position] = (28 + Math.floor(rnd() * 200)) * DAY_MS;
    } else {
      const u = q.units[0];
      const f = unitFactorOf(u);
      const mn = num(u?.min_value);
      const mx = num(u?.max_value);
      const ini = num(u?.initial_value) || num(q.initial_value);
      let v: number;
      if (!Number.isNaN(mn) && !Number.isNaN(mx)) v = middle ? (mn + mx) / 2 : mn + (mx - mn) * rnd();
      else if (!Number.isNaN(ini)) v = ini * (middle ? 1 : 0.5 + rnd());
      else v = middle ? 1 : rnd() * 100;
      a[q.position] = Number((v * f).toPrecision(6));
    }
  }
  return a;
}

interface Observed {
  /** Raw answerText of every sample in which the result was shown. */
  outs: { en: string; fa: string; weight: number }[];
}

function observe(data: CalculatorDetail): Map<number, Observed> {
  const seen = new Map<number, Observed>();
  for (const r of data.results) if (isDisplayedResult(r)) seen.set(r.position, { outs: [] });
  const rnd = makeRandom(12345);
  for (let i = 0; i < SAMPLES; i++) {
    const answers = sampleAnswers(data.questions, i === 0, rnd);
    const weight = Object.entries(answers).reduce((sum, [pos, v]) => {
      const q = data.questions.find((x) => x.position === Number(pos));
      return q && q.type === "multiple_choice" ? sum + v : sum;
    }, 0);
    let computed: ComputedResult[];
    try {
      computed = computeCalculator(data.questions, data.results, answers, { stringsFa: data.formula_strings_fa });
    } catch {
      continue;
    }
    for (const c of computed) {
      if (c.visible && c.answerText !== null) {
        seen.get(c.position)?.outs.push({ en: c.answerText, fa: c.answerTextFa ?? c.answerText, weight });
      }
    }
  }
  return seen;
}

function majorityKind(outs: Observed["outs"]): ValueKind | null {
  const counts = new Map<ValueKind, number>();
  for (const o of outs) {
    const k = valueKind(o.en);
    if (k !== "empty") counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  let best: ValueKind | null = null;
  let bestN = 0;
  for (const [k, n] of counts) {
    if (n > bestN) {
      best = k;
      bestN = n;
    }
  }
  return best;
}

function allWholeNumbers(outs: Observed["outs"]) {
  return outs.every((o) => {
    const v = Number(resultText(o.en));
    return Number.isFinite(v) && Number.isInteger(v);
  });
}

function spanOf(outs: Observed["outs"]) {
  const v = outs.map((o) => Number(resultText(o.en))).filter((x) => Number.isFinite(x));
  return v.length ? Math.max(...v) - Math.min(...v) : Infinity;
}

const DOSE_UNIT = /\b(mg|mcg|µg|μg|g|mL|ml|units?|IU|mEq|mmol|drops?|tablets?|cc|L|liters?)\b/i;
const DOSE_TITLE = /dos|rate|infus|volume|load|maint|fluid|bolus|deficit|replac/i;
const ACTION = /\b(required|recommend\w*|consider|should|imaging|refer|admit|discharge|treat\w*|x-?ray|radiograph\w*|biopsy|surgery|therapy|avoid|start|continue|stop|follow[- ]?up|screen(ing)? (is|not)|testing)\b/i;

const cache = new Map<string, ModelInfo>();

export function classifyCalculator(data: CalculatorDetail): ModelInfo {
  const hit = cache.get(data.slug);
  if (hit) return hit;
  const info = classify(data);
  cache.set(data.slug, info);
  return info;
}

function classify(data: CalculatorDetail): ModelInfo {
  if (data.questions.some((q) => q.type === "date_input")) return { model: "date" };

  const seen = observe(data);
  const rows = [...seen.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([position, o]) => ({ position, o, kind: majorityKind(o.outs), title: data.results.find((r) => r.position === position)?.title ?? "" }))
    .filter((r) => r.o.outs.length > 0 && r.kind !== null) as { position: number; o: Observed; kind: ValueKind; title: string }[];
  if (rows.length === 0) return { model: "plain" };

  if (rows.some((r) => r.kind === "tnm")) return { model: "staging" };

  const choices = data.questions.filter((q) => q.type === "multiple_choice").length;
  const numeric = data.questions.filter((q) => q.type !== "multiple_choice").length;
  const nums = rows.filter((r) => isNumeric(r.kind));
  const first = nums[0];
  const scoreLike =
    !!first && first.kind === "num" && allWholeNumbers(first.o.outs) && spanOf(first.o.outs) <= 100 && choices >= numeric;

  if (nums.length >= 3 && !(scoreLike && spanOf(first.o.outs) <= 80)) return { model: "panel" };

  if (first) {
    if (scoreLike) return { model: "score" };
    if (first.kind === "pct") return { model: "risk" };
    if (first.kind === "numunit") {
      const units = first.o.outs.map((o) => resultText(o.en)).join(" ");
      return { model: DOSE_UNIT.test(units) && DOSE_TITLE.test(`${first.title} ${data.name}`) ? "dose" : "measure" };
    }
    return { model: "index" };
  }

  const kinds = rows.map((r) => r.kind);
  if (kinds.includes("stage") && kinds.every((k) => k === "stage" || k === "label" || k === "mixed")) return { model: "staging" };

  if (kinds.includes("text")) {
    const heavy = rows.filter((r) => r.kind === "text").length;
    const longest = Math.max(...rows.flatMap((r) => r.o.outs.map((o) => resultText(o.en).length)));
    const bullets = Math.max(...rows.flatMap((r) => r.o.outs.map((o) => (resultText(o.en).match(/•|\n-/g) ?? []).length)));
    return { model: "narrative", narrative: heavy >= 3 || longest > 420 || bullets >= 3 ? "sections" : "headline" };
  }

  // A verdict: one label out of a fixed set.
  const main = rows.find((r) => r.kind === "label" || r.kind === "mixed") ?? rows[0];
  const byLabel = new Map<string, { en: string; fa: string; weight: number; n: number }>();
  for (const o of main.o.outs) {
    const key = resultText(o.en);
    const cur = byLabel.get(key);
    if (cur) {
      cur.weight += o.weight;
      cur.n += 1;
    } else {
      byLabel.set(key, { en: key, fa: resultText(o.fa), weight: o.weight, n: 1 });
    }
  }
  const labels = [...byLabel.values()].filter((l) => l.en);
  if (labels.some((l) => ACTION.test(l.en))) return { model: "verdict", verdict: "decision" };
  if (labels.length <= 2) return { model: "verdict", verdict: "yesno" };
  const ladder = labels
    .sort((a, b) => a.weight / a.n - b.weight / b.n)
    .map((l) => ({ en: l.en, fa: l.fa }));
  return { model: "verdict", verdict: "ladder", ladder };
}

// ---- reading a result's text --------------------------------------------

/** "12.5 mg/dL" -> number "12.5", rest "mg/dL". Comparators stay with the number. */
export function splitLeadingNumber(text: string): { value: string; rest: string } | null {
  const m = /^\s*([<>≤≥~]?\s*-?\d+(?:[.,]\d+)?(?:\s*-\s*\d+(?:[.,]\d+)?)?)\s*(.*)$/s.exec(resultText(text));
  return m ? { value: m[1].replace(/\s+/g, ""), rest: m[2].trim() } : null;
}

export interface MeasureValue {
  value: string;
  unit: string;
}

/** The value and its unit, and the same quantity in another unit when the
 * text itself carries one ("750 mmHg (100 kPa)" or "x/hour Or y/day"). */
export function parseMeasure(text: string): { main: MeasureValue; alts: MeasureValue[] } | null {
  const flat = resultText(text);
  const pieces: string[] = [];
  const parenthetical = /^(.*?)\s*\(([^()]*\d[^()]*)\)\s*$/s.exec(flat.replace(/\n/g, " "));
  if (/\n\s*or\s*\n/i.test(flat)) pieces.push(...flat.split(/\n\s*or\s*\n/i));
  else if (parenthetical) pieces.push(parenthetical[1], parenthetical[2]);
  else pieces.push(flat);
  const parsed = pieces
    .map((p) => splitLeadingNumber(p))
    .filter((p): p is { value: string; rest: string } => !!p)
    .map((p) => ({ value: p.value, unit: p.rest }));
  if (parsed.length === 0) return null;
  return { main: parsed[0], alts: parsed.slice(1) };
}

/** "4 Weeks 2 Days" -> {weeks: 4, days: 2}. */
export function parseAge(text: string): { weeks: number; days: number } | null {
  const flat = resultText(text).replace(/\n/g, " ");
  const w = /(\d+)\s*weeks?/i.exec(flat);
  const d = /(\d+)\s*days?/i.exec(flat);
  if (!w && !d) return null;
  return { weeks: w ? Number(w[1]) : 0, days: d ? Number(d[1]) : 0 };
}

const MONTH_INDEX: Record<string, number> = {
  jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12,
};

/** "November 9, 2026" or "May, 24 2027" -> a Gregorian date. */
export function parseDateText(text: string): { gy: number; gm: number; gd: number } | null {
  const m = /^([A-Za-z]{3})[a-z]*\.?,?\s+(\d{1,2}),?\s+(\d{4})$/.exec(resultText(text).replace(/\n/g, " "));
  if (!m) return null;
  const gm = MONTH_INDEX[m[1].toLowerCase()];
  return gm ? { gy: Number(m[3]), gm, gd: Number(m[2]) } : null;
}

/** Whether a yes/no style label reads as good news, bad news or neither. */
export function polarity(text: string): "ok" | "alert" | "neutral" {
  const t = text.toLowerCase();
  if (/\bnot\s+(low|normal)\b/.test(t)) return "alert";
  if (/\b(unlikely|not likely|negative|absent|normal|not required|not indicated|does not meet|do not meet|not meet|not consistent|not established|ruled out|no criteria|low risk|not (a )?risk)\b/.test(t)) return "ok";
  if (/\b(likely|probable|positive|present|meets|meet|definite|possible|high|severe|abnormal|required|consistent|established|yes)\b/.test(t)) return "alert";
  return "neutral";
}

/** T, N or M part of a TNM result ("pT2a", "cN1", "M0"), else null. */
export function tnmAxis(text: string): "T" | "N" | "M" | null {
  const m = /^(?:p|c|y|r)*([TNM])[0-4XxIiSs]\w{0,3}$/.exec(resultText(text));
  return m ? (m[1] as "T" | "N" | "M") : null;
}
