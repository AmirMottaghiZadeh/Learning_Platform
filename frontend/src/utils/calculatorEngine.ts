import { CalculatorQuestion, CalculatorResultDef } from "@/api/types";

/** Answers keyed by question position (`$0`, `$1`, ... in the source formulas). */
export type CalculatorAnswers = Record<number, number>;

/** A formula can resolve to a number (a score, a dose) or a plain string (a
 * risk-category label computed by the formula itself, e.g. "Higher risk of
 * health and social problems") -- both are valid, and later formulas can
 * reference either kind via `$resultN`. */
type ScopeValue = number | string;

export interface ComputedResult {
  position: number;
  title: string;
  visible: boolean;
  answerText: string | null;
}

/** Replace longer tokens first so `$result1` can't be swallowed by a `$1`
 * substring match, and `$1` can't be swallowed by `$10`. */
function substitute(template: string, scope: Record<string, ScopeValue>): string {
  let out = template;
  const tokens = Object.keys(scope).sort((a, b) => b.length - a.length);
  for (const token of tokens) {
    out = out.split(token).join(String(scope[token]));
  }
  return out;
}

/** The scoring formulas are plain JS IIFEs copied verbatim from the source
 * snapshot (e.g. `(function() { return $0 + $1; })();`) -- this is our own
 * bundled reference data, not user input, so evaluating it directly is the
 * same trust boundary as running any other code shipped in the app. */
function runRaw(formula: string, scope: Record<string, ScopeValue>): unknown {
  try {
    const substituted = substitute(formula, scope);
    // eslint-disable-next-line no-new-func
    const fn = new Function(`return ${substituted}`);
    return fn();
  } catch {
    return undefined;
  }
}

function runCondition(formula: string, scope: Record<string, ScopeValue>): boolean {
  return !!runRaw(formula, scope);
}

function formatNumber(value: number): string {
  return Number(value.toFixed(4)).toString();
}

/** Question types whose numeric mapping isn't implemented yet -- a calculator
 * containing one of these can't be safely computed (better to say so than to
 * silently guess at a medical score). */
export const UNSUPPORTED_QUESTION_TYPES: CalculatorQuestion["type"][] = ["date_input"];

export function hasUnsupportedQuestions(questions: CalculatorQuestion[]): boolean {
  return questions.some((q) => UNSUPPORTED_QUESTION_TYPES.includes(q.type));
}

export function computeCalculator(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
): ComputedResult[] {
  // A handful of formulas reference a unit-system toggle that lives outside
  // the question list on the source site (`$user_units == $si_units`) --
  // default all three to the same value so that comparison is stable and
  // picks the SI-labelled branch, since we don't build that toggle (yet).
  const scope: Record<string, ScopeValue> = { $user_units: 0, $si_units: 0, $us_units: 1 };
  for (const q of questions) {
    const value = answers[q.position];
    if (value !== undefined) scope[`$${q.position}`] = value;
  }

  const computed: ComputedResult[] = [];
  for (const r of [...results].sort((a, b) => a.position - b.position)) {
    const visible = r.condition_formula ? runCondition(r.condition_formula, scope) : true;
    const raw = r.formula ? runRaw(r.formula, scope) : undefined;
    const hasValue =
      (typeof raw === "number" && Number.isFinite(raw)) || typeof raw === "string";
    if (hasValue) scope[`$result${r.position}`] = raw as ScopeValue;

    let answerText: string | null = null;
    if (visible && hasValue) {
      if (r.answer) {
        answerText = substitute(r.answer, scope);
      } else {
        answerText = typeof raw === "number" ? formatNumber(raw) : String(raw);
      }
      // `answer` templates interpolate raw $resultN numbers -- format them
      // the same way as the bare-value fallback.
      answerText = answerText.replace(/-?\d+\.\d{5,}/g, (m) => formatNumber(Number(m)));
    }
    computed.push({ position: r.position, title: r.title, visible, answerText });
  }
  return computed;
}
