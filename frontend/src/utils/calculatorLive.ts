import { CalculatorDetail, CalculatorQuestion } from "@/api/types";

import { CalculatorAnswers, computeCalculator, extractNumericValue } from "./calculatorEngine";
import { isDisplayedResult, valueKind } from "./calculatorModel";

/** The pieces of a score calculator's live view that are pure logic: the
 * answers so far filled in, which result row is "the score", and what each
 * choice does to it. */

const num = (v: string | null | undefined) => (v === null || v === undefined || v === "" ? NaN : parseFloat(v));

/** The answers with every unanswered question filled in neutrally (a choice
 * with its lowest weight, a number with its lowest allowed value), so the
 * score can be shown before all questions are answered. */
export function filled(data: CalculatorDetail, answers: CalculatorAnswers, middle = false): CalculatorAnswers {
  const out: CalculatorAnswers = { ...answers };
  for (const q of data.questions) {
    if (out[q.position] !== undefined) continue;
    if (q.type === "multiple_choice") {
      const f = q.choices.map((c) => num(c.answer_factor)).filter((v) => !Number.isNaN(v));
      if (f.length) out[q.position] = middle ? f[Math.floor(f.length / 2)] : Math.min(...f);
    } else if (q.type === "numeric_input") {
      const u = q.units[0];
      const mn = num(u?.min_value);
      const mx = num(u?.max_value);
      const base = !Number.isNaN(mn) ? (middle && !Number.isNaN(mx) ? (mn + mx) / 2 : mn) : 0;
      out[q.position] = base * (u && u.unit_factor ? parseFloat(u.unit_factor) || 1 : 1);
    } else {
      out[q.position] = 0;
    }
  }
  return out;
}

/** A question's lowest and highest answer: its choices' weights, or a
 * number's allowed range. */
function extremes(q: CalculatorQuestion): [number, number] | null {
  if (q.type === "multiple_choice") {
    const f = q.choices.map((c) => num(c.answer_factor)).filter((v) => !Number.isNaN(v));
    return f.length ? [Math.min(...f), Math.max(...f)] : null;
  }
  if (q.type === "numeric_input") {
    const u = q.units[0];
    const factor = u && u.unit_factor ? parseFloat(u.unit_factor) || 1 : 1;
    const mn = num(u?.min_value);
    const mx = num(u?.max_value);
    return [(Number.isNaN(mn) ? 0 : mn) * factor, (Number.isNaN(mx) ? 100 : mx) * factor];
  }
  return null;
}

const primaryRows = new WeakMap<CalculatorDetail, number | null>();

/** The result the live score follows: of the shown rows that read as a
 * plain number, the one the most questions move -- the total, not a part of
 * it. Taking the first such row left the score box on Lund-Mackay's right
 * side, CMML CPSS-Mol's genetic subscore, MADIT-ICD's VT/VF score and one
 * PSQI component, so the other answers never changed it. */
export function primaryRow(data: CalculatorDetail): number | null {
  const cached = primaryRows.get(data);
  if (cached !== undefined) return cached;
  const shown = new Set(data.results.filter(isDisplayedResult).map((r) => r.position));
  const middle = filled(data, {}, true);
  const rows = computeCalculator(data.questions, data.results, middle, { stringsFa: data.formula_strings_fa })
    .filter((r) => shown.has(r.position) && valueKind(r.answerText) === "num")
    .map((r) => r.position);
  const moves = new Map(rows.map((p) => [p, 0]));
  if (rows.length > 1) {
    for (const q of data.questions) {
      const ends = extremes(q);
      if (!ends) continue;
      const moved = new Set<number>();
      for (const base of [middle, filled(data, {})]) {
        const [lo, hi] = ends.map((v) => computeCalculator(data.questions, data.results, { ...base, [q.position]: v }));
        for (const p of rows) {
          if (lo.find((r) => r.position === p)?.answerText !== hi.find((r) => r.position === p)?.answerText) moved.add(p);
        }
      }
      moved.forEach((p) => moves.set(p, (moves.get(p) ?? 0) + 1));
    }
  }
  const primary = rows.length ? rows.reduce((best, p) => ((moves.get(p) ?? 0) > (moves.get(best) ?? 0) ? p : best)) : null;
  primaryRows.set(data, primary);
  return primary;
}

/** What picking each choice of `question` does to the live score, for the
 * weight shown beside it -- read off the score itself, not the choice's
 * `answer_factor`. That is only the value the formula is handed, and the
 * formula may subtract it (EDACS hands "pain worse on inspiration" 4 and
 * scores it -4), scale it (WHO-5: x4), read it as a code (Blatchford's
 * haemoglobin bands, Child-Pugh) or leave it out of this score (PMR's
 * required criteria), so showing it as "+4" told the learner the opposite
 * of what the score then did. Each choice is measured against the
 * question's 0-weight choice (else its lowest), both with the learner's
 * other answers and with neutral ones. Null -- show no weights -- when a
 * choice moves the score by different amounts depending on the other
 * answers (a rule, a cap, a lookup): it has no one weight to show. */
export function choiceWeights(
  data: CalculatorDetail,
  question: CalculatorQuestion,
  answers: CalculatorAnswers,
): (number | null)[] | null {
  const primary = primaryRow(data);
  if (primary === null || question.type !== "multiple_choice") return null;
  const factors = question.choices.map((c) => num(c.answer_factor));
  const valid = factors.filter((f) => !Number.isNaN(f));
  if (valid.length < 2) return null;
  const reference = valid.includes(0) ? 0 : Math.min(...valid);

  const others = { ...answers };
  delete others[question.position];
  const bases = [filled(data, others), filled(data, others, true), filled(data, {}), filled(data, {}, true)];
  const scoreOf = (base: CalculatorAnswers, value: number) => {
    const text = computeCalculator(data.questions, data.results, { ...base, [question.position]: value }, { stopAfter: primary })
      .find((r) => r.position === primary)?.answerText;
    return text ? extractNumericValue(text) : null;
  };
  const baseline = bases.map((b) => scoreOf(b, reference));
  if (baseline.some((s) => s === null)) return null;

  const weights: (number | null)[] = [];
  for (const factor of factors) {
    if (Number.isNaN(factor)) {
      weights.push(null);
      continue;
    }
    const deltas = bases.map((b, i) => {
      const s = scoreOf(b, factor);
      return s === null ? NaN : s - (baseline[i] as number);
    });
    if (deltas.some((d) => Number.isNaN(d) || Math.abs(d - deltas[0]) > 1e-9)) return null;
    weights.push(Number(deltas[0].toFixed(4)));
  }
  return weights.some((w) => w !== null && w !== 0) ? weights : null;
}
