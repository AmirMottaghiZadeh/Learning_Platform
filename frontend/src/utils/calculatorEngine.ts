import { CalculatorErrorCheck, CalculatorQuestion, CalculatorResultDef, SectionTone } from "@/api/types";

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
  titleFa: string;
  visible: boolean;
  // Always both -- the caller picks which to show, and tone classification
  // / range sweeping always keys off the English one (see classifyResultTone
  // and computeResultRanges) regardless of what's displayed, since a
  // formula's own tone words ("High Risk") and the numeric value it computes
  // are both only ever produced in English -- there's no Persian formula
  // variant to run instead. `answerTextFa` falls back to the English text
  // when the source has no translated `answer_fa` template for this result.
  answerText: string | null;
  answerTextFa: string | null;
}

// Every token a scope can hold: `$<question>`, `$result<row>` and the
// three unit-system flags. One left-to-right pass with this pattern takes
// the longest match at each spot -- `$result1` is never read as `$` + ...,
// and `$10` never as `$1` + "0" -- which is what the old approach got by
// replacing tokens longest-first, one full split/join pass per token
// (dozens of passes over every formula, every evaluation: the dominant
// cost of the range search on 28-question calculators like SNAP-IV).
const SCOPE_TOKEN = /\$(?:result\d+|user_units|si_units|us_units|\d+)/g;

function substitute(template: string, scope: Record<string, ScopeValue>): string {
  return template.replace(SCOPE_TOKEN, (token) => {
    if (Object.prototype.hasOwnProperty.call(scope, token)) return String(scope[token]);
    // Same as the old passes for a token that isn't defined: its longest
    // defined prefix is still replaced ("$10" with only "$1" defined reads
    // as that value followed by "0").
    for (let end = token.length - 1; end > 1; end--) {
      const prefix = token.slice(0, end);
      if (Object.prototype.hasOwnProperty.call(scope, prefix)) return String(scope[prefix]) + token.slice(end);
    }
    return token;
  });
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

export function formatNumber(value: number): string {
  return Number(value.toFixed(4)).toString();
}

// A formula's returned text is sometimes a bucket like "&lt;1%" or "&ge;30%"
// (confirmed in 40+ results across the imported set, e.g. Framingham ATP-III,
// PORT Score, PECARN) -- plain `parseFloat` on that text returns NaN (it
// doesn't start with a digit), which silently drops the bucket from every
// range computation below, even though "less than 1%" / "at least 30%" is
// exactly the kind of boundary value a gauge's min/max needs. Stripping the
// leading comparator (its literal or HTML-entity form) and parsing what's
// left treats the threshold itself as that bucket's value, which is the
// right behaviour for a min/max *bound*, not an approximation of the bucket.
const LEADING_COMPARATOR = /^\s*(&lt;|&gt;|&le;|&ge;|<|>|≤|≥)\s*/;

export function extractNumericValue(text: string): number | null {
  const value = parseFloat(text.replace(LEADING_COMPARATOR, ""));
  return Number.isNaN(value) ? null : value;
}

function formatAnswerTemplate(template: string, scope: Record<string, ScopeValue>): string {
  // `answer`/`answer_fa` templates interpolate raw $resultN numbers -- format
  // them the same way as the bare-value fallback below.
  return substitute(template, scope).replace(/-?\d+\.\d{5,}/g, (m) => formatNumber(Number(m)));
}

/** Question types whose numeric mapping isn't implemented yet -- a calculator
 * containing one of these can't be safely computed (better to say so than to
 * silently guess at a medical score). */
export const UNSUPPORTED_QUESTION_TYPES: CalculatorQuestion["type"][] = ["date_input"];

export function hasUnsupportedQuestions(questions: CalculatorQuestion[]): boolean {
  return questions.some((q) => UNSUPPORTED_QUESTION_TYPES.includes(q.type));
}

/** Cross-field checks the source snapshot ships separately from the per-unit
 * min/max range (e.g. "systolic pressure must exceed diastolic") -- each
 * `formula` references raw answers only (`$0`, `$1`, ...), never a
 * `$resultN`, so these run once all questions are answered but before any
 * result is computed. A formula returning true means that check *failed*;
 * the first one that fails is returned (its `answer`/`answer_fa` is the
 * message to show), or null if every check passes. */
export function checkErrors(
  questions: CalculatorQuestion[],
  errorChecks: CalculatorErrorCheck[],
  answers: CalculatorAnswers,
): CalculatorErrorCheck | null {
  const scope: Record<string, ScopeValue> = { $user_units: 0, $si_units: 0, $us_units: 1 };
  for (const q of questions) {
    const value = answers[q.position];
    if (value !== undefined) scope[`$${q.position}`] = value;
  }
  for (const check of [...errorChecks].sort((a, b) => a.position - b.position)) {
    if (check.formula && runCondition(check.formula, scope)) return check;
  }
  return null;
}

type Translator = (text: string, scope: Record<string, ScopeValue>) => string;

const ESCAPES: Record<string, string> = { n: "\n", t: "\t", r: "\r", '"': '"', "'": "'", "\\": "\\" };
// Map keys are the literals as written in formula source, so `\n` there is
// a backslash and an "n" while the string the formula returns has a real
// newline; whitespace runs also differ (23 keys carry a double space).
const unescapeLiteral = (s: string) => s.replace(/\\([ntr"'\\])/g, (_, c: string) => ESCAPES[c]);
const squash = (s: string) => s.replace(/\s+/g, " ").trim();
const PLACEHOLDER = /\$\{[^}]*\}/g;
const latinLetters = (s: string) => (s.match(/[A-Za-z]/g) ?? []).length;
const escapeForRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const translators = new WeakMap<Record<string, string>, Translator>();

/** Persian for a string a formula returned, from the calculator's own
 * `formula_strings_fa` (English literal -> translation, 1,621 of them over
 * 305 calculators). Tried in order:
 *  1. the whole string, after undoing source escapes and squashing spaces;
 *  2. keys that embed a value -- `$result0` ("EDACS is $result0. ...") is
 *     filled from this evaluation's scope, and a JS template placeholder
 *     (`${quotient} (Probably Thalassemia.)`) is matched as a wildcard and
 *     the same captured text carried into the translation;
 *  3. a string the formula glued together from several literals (Centor:
 *     `msg += "..."; msg += "..."`) -- each known literal replaced where it
 *     stands as whole words, longest first, kept only if that removes most
 *     of the English (otherwise half-translated text would be worse than
 *     the original).
 * Anything unmatched stays as the formula produced it -- never guessed. */
function translatorFor(map: Record<string, string>): Translator {
  const cached = translators.get(map);
  if (cached) return cached;

  const exact = new Map<string, string>();
  const templated: { key: string; fa: string }[] = [];
  for (const [rawKey, rawFa] of Object.entries(map)) {
    const key = squash(unescapeLiteral(rawKey));
    const fa = unescapeLiteral(rawFa);
    // An entry "translated" to itself (`T${Therapy}D5N2`, `${points}.
    // ${DENOVA_score}`) carries nothing -- and as a placeholder pattern it
    // would match almost any sentence and hand it back in English, ahead
    // of the steps that could really translate it.
    if (!key || squash(fa) === key) continue;
    if (key.includes("$")) {
      // A pattern needs real words of its own to be specific to one text.
      if (latinLetters(key.replace(PLACEHOLDER, "").replace(SCOPE_TOKEN, "")) >= 3) templated.push({ key, fa });
    } else {
      exact.set(key, fa);
    }
  }
  const fragments = [...exact.entries()].filter(([k]) => k.length >= 3).sort((a, b) => b[0].length - a[0].length);
  const memo = new Map<string, string>();

  const viaTemplates = (s: string, scope: Record<string, ScopeValue>): string | null => {
    for (const { key, fa } of templated) {
      const filledKey = squash(substitute(key, scope));
      const filledFa = substitute(fa, scope);
      const names = filledKey.match(PLACEHOLDER) ?? [];
      if (names.length === 0) {
        if (filledKey === s) return filledFa;
        continue;
      }
      const pattern = filledKey.split(PLACEHOLDER).map(escapeForRegExp).join("(.+?)");
      const m = new RegExp(`^${pattern}$`).exec(s);
      if (!m) continue;
      const captured = new Map(names.map((name, i) => [name, m[i + 1]] as const));
      return filledFa.replace(PLACEHOLDER, (name) => captured.get(name) ?? name);
    }
    return null;
  };

  const viaFragments = (s: string): string | null => {
    let out = s;
    for (const [key, fa] of fragments) {
      let idx = out.indexOf(key);
      while (idx >= 0) {
        const before = out[idx - 1];
        const after = out[idx + key.length];
        if ((!before || !/[A-Za-z0-9]/.test(before)) && (!after || !/[A-Za-z0-9]/.test(after))) {
          out = out.slice(0, idx) + fa + out.slice(idx + key.length);
          idx = out.indexOf(key, idx + fa.length);
        } else {
          idx = out.indexOf(key, idx + 1);
        }
      }
    }
    const before = latinLetters(s);
    return before > 0 && out !== s && latinLetters(out) <= before * 0.4 ? out : null;
  };

  const translator: Translator = (text, scope) => {
    const s = squash(text);
    const direct = exact.get(s);
    if (direct !== undefined) return direct;
    const templatedHit = templated.length ? viaTemplates(s, scope) : null;
    if (templatedHit !== null) return templatedHit;
    let hit = memo.get(s);
    if (hit === undefined) {
      hit = viaFragments(s) ?? text;
      memo.set(s, hit);
    }
    return hit;
  };
  translators.set(map, translator);
  return translator;
}

/** A bare answer template pointing at a LATER row ("$result1" on row 0)
 * can never resolve -- rows fill in order, so it showed the literal text
 * "$result1" in the result box. Across the imported set every such
 * template (124 of them, all bare -- none embedded in other text) is the
 * source counting rows from 1 instead of 0 (Boston/Rochester Criteria,
 * Light's Criteria, part of CKD Management and PSQI...): row 0's
 * "$result1" means row 0's own value, Light's last row even names a
 * "$result3" that doesn't exist. Read it as this row's own value. A bare
 * reference to an EARLIER row (ABCD²'s summary row showing "$result0") is
 * a real, working cross-reference and is left alone. */
function selfTemplate(template: string | null | undefined, position: number): string | null | undefined {
  const m = template ? /^\s*\$result(\d+)\s*$/.exec(template) : null;
  return m && Number(m[1]) > position ? `$result${position}` : template;
}

export interface ComputeOptions {
  /** Forces `$result<position>` to a chosen value instead of running that
   * row's own formula -- used only by computeTierBands, to ask "what would
   * the calculator's OTHER rows say if this score were X" without needing
   * a real answer combination that actually produces X. */
  overrides?: Record<number, number>;
  /** Stop after this result position -- the tier sweep only needs rows up
   * to the interpretation it's reading, and later rows can't affect it
   * (rows evaluate strictly in order). */
  stopAfter?: number;
  /** The calculator's `formula_strings_fa`: Persian for text a formula
   * returns itself (see translatorFor). Without it, `answerTextFa` for
   * such a row is the English text. */
  stringsFa?: Record<string, string>;
}

export function computeCalculator(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  { overrides, stopAfter, stringsFa }: ComputeOptions = {},
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
  // Formulas always run on the English values -- they compare their own
  // strings (`$result1 == "Positive"`) -- so translation only ever feeds a
  // parallel scope used for the Persian answer template.
  const translate = stringsFa ? translatorFor(stringsFa) : null;
  const scopeFa: Record<string, ScopeValue> = { ...scope };

  const computed: ComputedResult[] = [];
  for (const r of [...results].sort((a, b) => a.position - b.position)) {
    if (stopAfter !== undefined && r.position > stopAfter) break;
    const visible = r.condition_formula ? runCondition(r.condition_formula, scope) : true;
    const override = overrides?.[r.position];
    const raw = override !== undefined ? override : r.formula ? runRaw(r.formula, scope) : undefined;
    const hasValue =
      (typeof raw === "number" && Number.isFinite(raw)) || typeof raw === "string";
    const rawFa = typeof raw === "string" && translate ? translate(raw, scope) : raw;
    if (hasValue) {
      scope[`$result${r.position}`] = raw as ScopeValue;
      scopeFa[`$result${r.position}`] = rawFa as ScopeValue;
    }

    let answerText: string | null = null;
    let answerTextFa: string | null = null;
    if (visible && hasValue) {
      const template = selfTemplate(r.answer, r.position);
      const templateFa = selfTemplate(r.answer_fa, r.position);
      answerText = template
        ? formatAnswerTemplate(template, scope)
        : typeof raw === "number" ? formatNumber(raw) : String(raw);
      answerTextFa = templateFa
        ? formatAnswerTemplate(templateFa, scopeFa)
        : template ? answerText : typeof rawFa === "number" ? formatNumber(rawFa) : String(rawFa);
    }
    computed.push({
      position: r.position,
      title: r.title,
      titleFa: r.title_fa || r.title,
      visible,
      answerText,
      answerTextFa,
    });
  }
  return computed;
}

// These calculators are Medscape/QxMD source data -- their formulas already
// return risk-tier words as plain English text (e.g. `return "High Risk";`,
// confirmed across the imported set: "risk" alone appears in ~165 distinct
// return strings, "high"/"moderate"/"intermediate" in dozens more), and that
// literal text has no Persian counterpart (formulas aren't translated, only
// the surrounding template around them is -- see ComputedResult). Always
// classify from the English text for that reason, regardless of which
// language is displayed. Recognizing that existing vocabulary and giving it
// the same tone language already used for drug warnings elsewhere in the app
// is not inventing a clinical judgment -- it's just surfacing the one the
// calculator's own formula already made.
const DANGER_PATTERN = /\b(high|severe|critical|abnormal)\b/i;
const CAUTION_PATTERN = /\b(moderate|intermediate|mild|borderline|elevated)\b/i;

/** `null` means no reliable tone signal in the text -- the caller should
 * keep its default (neutral) styling rather than guess. Always pass the
 * English `answerText`, even when displaying `answerTextFa`. */
export function classifyResultTone(text: string): SectionTone | null {
  if (DANGER_PATTERN.test(text)) return "deny";
  if (CAUTION_PATTERN.test(text)) return "caution";
  return null;
}

/** One contiguous stretch of `[from, to]` within a result's range where the
 * calculator's own dependent row (see dependentTextPosition) says the same
 * thing -- e.g. ASDAS-CRP's score legitimately crosses "Inactive Disease",
 * "Moderate", "High" and "Very High" as it sweeps its own min to max, and a
 * single min/max caption pair was hiding every band in between. Built by
 * computeResultBands; never invented, since `text`/`textFa` are always
 * read verbatim from that row's own real output. */
export interface ScoreBand {
  from: number;
  to: number;
  text: string;
  textFa: string;
}

export interface ResultRange {
  min: number;
  max: number;
  /** True when this side of the scale has no real limit -- the result
   * depends on a question with no bound (a lab value, age, height), so
   * `min`/`max` on that side is only drawing room for the open-ended
   * outermost tier, not a number the scale actually stops at. The gauge
   * labels such an end with its cutoff as an inequality ("< 1.3",
   * "> 57") instead of printing `min`/`max`. */
  minOpen: boolean;
  maxOpen: boolean;
  /** Empty when nothing in the calculator's own data describes any point
   * in this range (no row anywhere reads this result's `$resultN` back) --
   * the gauge then falls back to one neutral arc, same as before bands
   * existed. */
  bands: ScoreBand[];
}

// Below this many combinations, every one of them is actually evaluated --
// an exhaustive sweep, not a guess. Above it (most real calculators: 10+
// multiple-choice questions, or any numeric question's own dense grid
// (NUMERIC_RANGE_SAMPLE_POINTS), routinely multiply out past a million),
// that's no longer practical -- see heuristicResultRanges below for what
// runs instead.
const MAX_RANGE_COMBINATIONS = 3000;

// A numeric question's true min/max contribution to a result doesn't
// always sit at its own endpoint -- several real formulas (APACHE II's
// physiologic-deviation points, PSI's temperature band) add the *most*
// points at BOTH extremes and the *least* at an interior "normal" value
// (confirmed against real data: endpoint-only sampling computed APACHE II's
// range as 10-60 when the calculator's own documented range is 0-71).
// Sampling a grid across the whole range -- not just its two ends -- lets
// the sweep below find that interior optimum too, to the grid's resolution.
const NUMERIC_RANGE_SAMPLE_POINTS = 21;

/** `null` only when this question has neither a real bound NOR an answer to
 * pin it to -- shouldn't happen by the time ranges are computed (every
 * question is validated as answered first), but kept as the genuine
 * "can't compute anything" case. A question with no real bound (a free-text
 * lab value with no sensible max, e.g. CRP) is pinned to the learner's own
 * answer instead of blocking the whole calculator's range: confirmed
 * against real data (ASDAS-CRP) that this is common -- one bounded
 * multi-question clinical score plus one unbounded lab value -- and without
 * pinning, that one question blocked every result's gauge, including ones
 * that don't even depend on it. The resulting range is exact *given that
 * answer*, not an estimate -- just narrower in scope than a fully general
 * range (which doesn't exist for an unbounded question anyway). `pinned`
 * marks exactly that case, so a result that depends on such a question
 * is known to have no real scale limit (see ResultRange.minOpen). */
function questionDomain(
  q: CalculatorQuestion,
  answers: CalculatorAnswers,
): { values: number[]; pinned: boolean } | null {
  if (q.type === "multiple_choice") {
    const values = q.choices
      .map((c) => (c.answer_factor !== null ? parseFloat(c.answer_factor) : NaN))
      .filter((v) => !Number.isNaN(v));
    if (values.length > 0) return { values, pinned: false };
  } else {
    const unit = q.units[0];
    const min = unit?.min_value !== null && unit?.min_value !== undefined ? parseFloat(unit.min_value) : NaN;
    const max = unit?.max_value !== null && unit?.max_value !== undefined ? parseFloat(unit.max_value) : NaN;
    if (!Number.isNaN(min) && !Number.isNaN(max)) {
      if (min === max) return { values: [min], pinned: false };
      const points: number[] = [];
      for (let i = 0; i < NUMERIC_RANGE_SAMPLE_POINTS; i++) {
        points.push(min + ((max - min) * i) / (NUMERIC_RANGE_SAMPLE_POINTS - 1));
      }
      return { values: points, pinned: false };
    }
  }
  const answered = answers[q.position];
  return answered !== undefined ? { values: [answered], pinned: true } : null;
}

/** Whether this result actually moves with a pinned question -- a
 * calculator can have an unbounded question that only some of its
 * results read, and only those results lose a real scale limit. Probed
 * by nudging the answer both ways rather than parsing the formula text,
 * which can reach the question through any chain of `$resultN`. */
function dependsOnQuestion(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  targetPosition: number,
  questionPosition: number,
  value: number,
): boolean {
  const base = answers[questionPosition];
  for (const nudged of [base * 1.37 + 0.71, base * 0.63]) {
    const c = computeCalculator(questions, results, { ...answers, [questionPosition]: nudged })
      .find((x) => x.position === targetPosition);
    const v = c && c.visible && c.answerText !== null ? extractNumericValue(c.answerText) : null;
    if (v === null || Math.abs(v - value) > 1e-9) return true;
  }
  return false;
}

function* cartesian(
  domains: { position: number; values: number[] }[],
  i = 0,
  acc: CalculatorAnswers = {},
): Generator<CalculatorAnswers> {
  if (i === domains.length) {
    yield acc;
    return;
  }
  for (const v of domains[i].values) {
    yield* cartesian(domains, i + 1, { ...acc, [domains[i].position]: v });
  }
}

type MinMax = { min: number; max: number };

// Past this many distinct values a result is effectively continuous, and
// sampling its interpretation at every one of them buys nothing over the
// grid in computeTierBands.
const REACHABLE_VALUES_CAP = 1000;

function sweepCombinations(
  combos: Iterable<CalculatorAnswers>,
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  tracking: Map<number, MinMax>,
  // Every distinct value each result actually took across the sweep (null
  // once past REACHABLE_VALUES_CAP) -- the exact set an exhaustive sweep
  // already visits, so tiers can be read at exactly those values instead
  // of guessing a sampling lattice (see computeTierBands).
  reachable?: Map<number, Set<number> | null>,
): void {
  for (const answers of combos) {
    const computed = computeCalculator(questions, results, answers);
    for (const c of computed) {
      // Always the English text for the swept value itself -- see
      // ComputedResult on why numeric extraction must not run against a
      // Persian-templated string.
      if (!c.visible || c.answerText === null) continue;
      const value = extractNumericValue(c.answerText);
      if (value === null) continue;

      if (reachable) {
        const prior = reachable.get(c.position);
        if (prior !== null) {
          const seen = prior ?? new Set<number>();
          seen.add(value);
          reachable.set(c.position, seen.size > REACHABLE_VALUES_CAP ? null : seen);
        }
      }

      const existing = tracking.get(c.position);
      if (!existing) {
        tracking.set(c.position, { min: value, max: value });
        continue;
      }
      if (value < existing.min) existing.min = value;
      if (value > existing.max) existing.max = value;
    }
  }
}

type Domain = { position: number; values: number[] };

/** A handful of starting combinations for the coordinate-descent search
 * below. "Every dimension at its own raw min/max" is the old heuristic's
 * ENTIRE strategy, kept as two of these seeds -- correct only when every
 * question's raw factor value happens to move the result in the same
 * direction as every other (confirmed false against real data: Framingham's
 * female-sex term is -1, a male-high-risk combo isn't the true max once sex
 * can flip; a 2-numeric-term product like days-per-week x minutes-per-day
 * is minimized by EITHER being 0, which both the raw-min and raw-max seeds
 * hit when the other factor's own raw endpoint happens to be 0 -- descent
 * from a single deterministic seed can get stuck exactly there, since
 * moving one factor alone while the other is 0 never looks like an
 * improvement). The random restarts exist to escape exactly that trap: a
 * random combination is very unlikely to zero out two factors at once, and
 * once off zero, descent can actually see each factor's real effect. */
function buildHeuristicSeeds(domains: Domain[]): CalculatorAnswers[] {
  const allLow: CalculatorAnswers = {};
  const allHigh: CalculatorAnswers = {};
  const firstEach: CalculatorAnswers = {};
  const lastEach: CalculatorAnswers = {};
  for (const d of domains) {
    allLow[d.position] = Math.min(...d.values);
    allHigh[d.position] = Math.max(...d.values);
    firstEach[d.position] = d.values[0];
    lastEach[d.position] = d.values[d.values.length - 1];
  }
  const seeds = [allLow, allHigh, firstEach, lastEach];
  for (let i = 0; i < 6; i++) {
    const seed: CalculatorAnswers = {};
    for (const d of domains) seed[d.position] = d.values[Math.floor(Math.random() * d.values.length)];
    seeds.push(seed);
  }
  return seeds;
}

/** This target result's numeric value at `answers`, or null if it isn't
 * visible there or its text carries no number (see extractNumericValue). */
function evaluateResultAt(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  targetPosition: number,
): number | null {
  const c = computeCalculator(questions, results, answers, { stopAfter: targetPosition })
    .find((x) => x.position === targetPosition);
  if (!c || !c.visible || c.answerText === null) return null;
  return extractNumericValue(c.answerText);
}

const COORDINATE_DESCENT_PASSES = 4;

/** Starting from `seed`, repeatedly sweeps every dimension in turn, locking
 * in whichever of that dimension's own candidate values most improves (for
 * `direction`) the target result -- re-sweeping earlier dimensions against
 * each new value, so a later dimension's move can still unlock a better
 * choice for an earlier one (unlike a single independent per-dimension
 * probe). Exact for a result that's a monotonic function of a sum of
 * per-question terms (the same guarantee the old heuristic claimed, now
 * actually delivered); a best-effort (not a proven global optimum, but
 * never worse than the seed) for a formula with real cross-question
 * interaction, same as the old heuristic already assumed away. */
function coordinateDescentCombo(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  domains: Domain[],
  targetPosition: number,
  seed: CalculatorAnswers,
  direction: "min" | "max",
): { combo: CalculatorAnswers; value: number } | null {
  let combo = { ...seed };
  let seedValue = evaluateResultAt(questions, results, combo, targetPosition);
  if (seedValue === null) {
    // The seed itself doesn't even produce a visible/numeric value for this
    // result (e.g. it's gated by a condition on another question) -- a
    // neutral combo is at least a defined starting point to descend from.
    combo = {};
    for (const d of domains) combo[d.position] = d.values[0];
    seedValue = evaluateResultAt(questions, results, combo, targetPosition);
    if (seedValue === null) return null;
  }
  let value: number = seedValue;
  for (let pass = 0; pass < COORDINATE_DESCENT_PASSES; pass++) {
    let improved = false;
    for (const d of domains) {
      let bestCandidate = combo[d.position];
      let bestValue = value;
      for (const candidate of d.values) {
        if (candidate === combo[d.position]) continue;
        const trialValue = evaluateResultAt(questions, results, { ...combo, [d.position]: candidate }, targetPosition);
        if (trialValue === null) continue;
        if ((direction === "min" && trialValue < bestValue) || (direction === "max" && trialValue > bestValue)) {
          bestValue = trialValue;
          bestCandidate = candidate;
        }
      }
      if (bestCandidate !== combo[d.position]) {
        combo = { ...combo, [d.position]: bestCandidate };
        value = bestValue;
        improved = true;
      }
    }
    if (!improved) break;
  }
  return { combo, value };
}

/** The >MAX_RANGE_COMBINATIONS case: a true exhaustive sweep is no longer
 * affordable, so each result's min and max are found independently by
 * coordinate descent from several seeds (see buildHeuristicSeeds), keeping
 * the best outcome across all of them. Verified against real imported data
 * by comparing its output to Monte Carlo sampling (which can't miss a
 * combination this search also tried) across every calculator this branch
 * applies to: closed every case the old single-pair heuristic got
 * measurably wrong (APACHE II's range was 10-60 instead of the documented
 * 0-71; Pneumonia Severity Index's top gauge band collapsed to a single
 * point; several others silently excluded their own true extreme). */
function heuristicResultRanges(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  domains: Domain[],
): Map<number, MinMax> {
  const seeds = buildHeuristicSeeds(domains);
  const tracking = new Map<number, MinMax>();

  for (const r of results) {
    const pos = r.position;
    let best: number | null = null;
    let worst: number | null = null;
    for (const seed of seeds) {
      const lo = coordinateDescentCombo(questions, results, domains, pos, seed, "min");
      if (lo && (worst === null || lo.value < worst)) worst = lo.value;
      const hi = coordinateDescentCombo(questions, results, domains, pos, seed, "max");
      if (hi && (best === null || hi.value > best)) best = hi.value;
    }
    if (best === null || worst === null) continue;
    tracking.set(pos, { min: Math.min(worst, best), max: Math.max(worst, best) });
  }
  return tracking;
}

// Fine enough to catch every real band boundary found in the imported set
// (the narrowest, Framingham's 1-point-wide risk-% buckets, are still
// several grid steps apart over that result's ~30-point range) without
// resampling per-question combinations again -- this only re-evaluates the
// dependent row itself, holding every answer at the learner's real one.
const BAND_SAMPLE_POINTS = 61;

// A result whose min AND max are both whole numbers is, in every example
// in the imported set, actually constrained to WHOLE numbers throughout
// (an integer point total; a 0/1/2 coded category) -- evenly spaced
// *fractional* samples between them ask the dependent row about values
// that can never really occur, and a row written as a chain of `==`
// checks (Framingham's own risk-group code, not its final result) then
// silently falls through to whatever its "else" branch says, producing
// fake band edges at those fractional points. Sampling every integer
// instead (bounded, so one calculator can't blow this up) asks only
// genuinely achievable questions. A non-integer range (ASDAS-CRP's score
// is a weighted float composite, confirmed real min/max like 1.27-4.87)
// keeps the even fractional grid, which is the right one for it.
const INTEGER_BAND_SAMPLE_CAP = 400;

function isWholeNumber(v: number): boolean {
  return Math.abs(v - Math.round(v)) < 1e-6;
}

/** More bands than this isn't a categorical interpretation any more. Set
 * above the widest genuine table found in the imported set -- Framingham
 * ATP-III's risk-% ladder is 14 rungs ("&lt;1%" up through "&ge;30%", one
 * per point for a while, confirmed by direct enumeration) and is exactly
 * the kind of result this whole feature exists to show, so the cap must
 * clear it with room to spare. Past it, a row is doing arithmetic with
 * the score (a different unit of the same continuous quantity) rather
 * than classifying it, and a gauge painted in 40 unreadable slivers is
 * worse than showing none. */
const MAX_SENSIBLE_BANDS = 20;

const NUMBER_SPLIT = /(-?\d+(?:\.\d+)?)/;

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** The exact numeric cutoffs a dependent row's own formula compares
 * `$result<targetPosition>` against (e.g. Aortic Stenosis Risk Score's
 * "if ($result0 > 57) ... else if ($result0 >= 7) ..." yields [57, 7]) --
 * read directly out of its source text with a regex, never approximated
 * from sampling. Matches either operand order (`$resultN > 7` and
 * `7 < $resultN` both found) and every comparison operator, and follows
 * a local alias of the token too: real rows often copy it into a variable
 * first (MDS Frailty: `var FI = $result0; if (FI > 0.4)`; Brain
 * Metastases: `var gpa = $result0; if (gpa >= 3.5)`), which a search for
 * `$result0` alone never saw -- those calculators' bands were then only
 * as exact as a sample grid's resolution. */
function extractThresholds(formulaText: string, targetPosition: number): number[] {
  const tokenRef = `\\$result${targetPosition}(?![\\w$])`;
  const forwardRefs = [tokenRef];
  const backwardRefs = [tokenRef];
  // Only a plain copy is an alias -- `var avg = $result0 / 9.0` is a
  // DIFFERENT quantity (SNAP-IV compares avg > 2.56, i.e. 23.04 on the
  // score), and its constants must not be taken as the score's cutoffs.
  const alias = new RegExp(`(?:var|let|const)\\s+([A-Za-z_$][\\w$]*)\\s*=\\s*${tokenRef}(?=\\s*(?:;|,|\\r?\\n|$))`, "g");
  let a: RegExpExecArray | null;
  while ((a = alias.exec(formulaText))) {
    const name = escapeRegExp(a[1]);
    forwardRefs.push(`(?:^|[^\\w$.])${name}(?![\\w$])`);
    backwardRefs.push(`${name}(?![\\w$])`);
  }
  const number = "(-?\\d+(?:\\.\\d+)?)";
  const op = "(?:===|!==|==|!=|>=|<=|>|<)";
  // Parentheses may wrap either side (Edinburgh writes `(($result0) >= 10)`).
  const patterns = [
    ...forwardRefs.map((ref) => new RegExp(`${ref}[\\s)]*${op}[\\s(]*${number}`, "g")),
    ...backwardRefs.map((ref) => new RegExp(`${number}[\\s)]*${op}[\\s(]*${ref}`, "g")),
  ];
  const thresholds: number[] = [];
  for (const re of patterns) {
    let m: RegExpExecArray | null;
    while ((m = re.exec(formulaText))) {
      const v = parseFloat(m[1]);
      if (!Number.isNaN(v)) thresholds.push(v);
    }
  }
  return thresholds;
}

/** A sampled meaning that can stand as a tier's label at all -- not a
 * bare number (that's arithmetic, not an interpretation: a rounded echo,
 * a sub-total, a 0/1/2 code -- confirmed real: Lund-Mackay's
 * `$result0 + $result1`, Sokal's `return $result0;`) and not a broken
 * computation ("NaN mL/kg" when a lab value is zero). A number WITH
 * words or a unit ("2.8 %", "3 Months") is a real tier value. */
function isUsableMeaning(text: string): boolean {
  const plain = text.replace(/<[^>]*>/g, " ").replace(/&[a-z#0-9]+;/gi, " ").trim();
  if (!plain || /^(?:NaN|-?Infinity|undefined|null)\b/i.test(plain)) return false;
  return !/^[-+]?\d+(?:\.\d+)?$/.test(plain);
}

// Close enough to call a number in a sampled label "the swept value
// itself printed back" -- covers the engine's 4-decimal formatting and a
// row rounding it to one decimal before printing.
const ECHO_TOLERANCE = 0.051;

function findEcho(parts: string[], value: number): number {
  for (let i = 1; i < parts.length; i += 2) {
    if (Math.abs(parseFloat(parts[i]) - value) <= ECHO_TOLERANCE) return i;
  }
  return -1;
}

/** The label with the echoed score masked out, for grouping -- null when
 * this label doesn't print the score back at all. */
function echoKey(text: string, value: number): string | null {
  const parts = text.split(NUMBER_SPLIT);
  const i = findEcho(parts, value);
  if (i < 0) return null;
  parts[i] = "#";
  return parts.join("");
}

/** The label with the echoed score removed, for display: the sentence it
 * sat in goes with it ("EDACS is -27.8. EDACS < 16, ..." -> "EDACS < 16,
 * ..."), unless it's the only sentence -- then just the number and its
 * dangling separator ("-19.87 - Low risk" -> "Low risk"). */
function stripEcho(text: string, value: number): string {
  const parts = text.split(NUMBER_SPLIT);
  const i = findEcho(parts, value);
  if (i < 0) return text;
  parts[i] = "\u0000";
  const pieces = parts.join("").split(/(\.\s+)/);
  const sentences: string[] = [];
  for (let k = 0; k < pieces.length; k += 2) sentences.push(pieces[k] + (pieces[k + 1] ?? ""));
  const kept = sentences.length > 1 ? sentences.filter((s) => !s.includes("\u0000")) : sentences;
  const label = (kept.length ? kept : sentences)
    .join("")
    .replace(/\u0000/g, "")
    .replace(/\s{2,}/g, " ")
    .replace(/^[\s\-–—:·|,.]+/, "")
    .replace(/[\s\-–—:·|,]+$/, "")
    .trim();
  return label || text;
}

/** Slices `[min, max]` into contiguous bands of identical meaning by
 * sampling a grid, UNIONED with `extraPoints` (the dependent row's own
 * exact threshold constants, from extractThresholds) so a boundary lands
 * on the real cutoff (57, 7, 1.3, ...) instead of wherever the grid
 * happened to fall -- a plain even grid alone can only approximate it to
 * its own resolution, and a chain that mixes `==` point-checks with `<`
 * range-checks (2HELPS2B: "$result0==0 ... ==1 ... >1") needs the regular
 * grid regardless, since a point-check can only ever be satisfied by
 * landing on that exact integer, never a formula-derived interval
 * midpoint (confirmed against real data: evaluating only at the midpoint
 * between consecutive extracted constants silently dropped every `==`
 * band -- 2HELPS2B's "No Further"/"12-Hour" tiers, Framingham's dozen
 * 1%-wide risk buckets -- because 4.5 satisfies none of `==0`, `==1`,
 * ..., `==11`). Asks the calculator's own dependent row (meaningPosition)
 * what it says at every sampled value -- via computeCalculator's
 * `overrides`, so every OTHER answer (including any the dependent row
 * also reads directly, e.g. PORT Score's age-gated lowest tier) stays the
 * learner's real one. Never invented: `text`/`textFa` are always that
 * row's own real output; a sample where the dependent row isn't visible,
 * returns no text, or returns no usable meaning (isUsableMeaning) is
 * simply dropped, not guessed at.
 *
 * A row that prints the score back inside each label ("EDACS is -27.8.
 * EDACS < 16, ..."; MDS Frailty's "-19.87 - Low risk") makes every
 * sample's text unique, so plain grouping never finds a tier (confirmed:
 * both read as 400 distinct "tiers" and were dropped). When nearly every
 * sample's label contains the swept value itself, grouping ignores that
 * one number and the label drops it (see stripEcho). Returns [] when
 * fewer than two tiers, or more than MAX_SENSIBLE_BANDS, come out --
 * neither is a categorical interpretation. */
function computeTierBands(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  targetPosition: number,
  meaningPosition: number,
  min: number,
  max: number,
  extraPoints: number[] = [],
  // A result that's inherently continuous (a percentage) can have
  // whole-number BOUNDS (0 to 100) without the quantity itself being
  // integer-stepped -- forces the fractional branch even then, since the
  // integer branch would otherwise sample only 0,1,2,...,100 and miss
  // that this chain's cutoff is a strict `>`, whose true transition sits
  // between two whole numbers (57 is still "Intermediate", 58 is
  // "High"), leaving a 1-unit gap neither band covers.
  forceContinuous = false,
  // Every value this result can actually take, when an exhaustive sweep
  // knows them (closed scale) -- read the interpretation at exactly these
  // and nothing else. Any lattice guessed from min/max is wrong for some
  // real score: McMahon Rhabdomyolysis runs 0 to 19 but moves in HALF
  // points, so whole-number bounds made the integer lattice skip every
  // x.5 rung ("1.8%", "2.7%", ...); a fractional grid instead asks about
  // values no patient can produce.
  exactValues: number[] | null = null,
  // So each band's Persian label is the real translation (see
  // translatorFor), not the English text repeated.
  stringsFa?: Record<string, string>,
): ScoreBand[] {
  if (!(max > min)) return [];

  let sampleValues: number[];
  if (exactValues && exactValues.length > 0) {
    sampleValues = exactValues.filter((v) => v >= min && v <= max);
  } else if (
    !forceContinuous
    && isWholeNumber(min)
    && isWholeNumber(max)
    && extraPoints.every(isWholeNumber)
    && max - min + 1 <= INTEGER_BAND_SAMPLE_CAP
  ) {
    // Every achievable value here is already a whole number -- inserting
    // a fractional probe around an extracted threshold (below) would ask
    // about a value that can never really occur and, worse, can fall
    // through every `==` branch of a chain like Framingham's into
    // whatever its catch-all "else" says, fabricating a hairline band
    // that doesn't correspond to anything real (confirmed: a probe at
    // 23.999999 for a female-branch cutoff of 24 hit no `==` check and
    // read back that chain's unrelated top-tier "else"). The integer
    // grid already samples every one of this threshold's neighbours
    // exactly, so it needs no help landing on it.
    sampleValues = [];
    for (let v = Math.round(min); v <= Math.round(max); v++) sampleValues.push(v);
  } else {
    const base: number[] = [];
    for (let i = 0; i < BAND_SAMPLE_POINTS; i++) {
      base.push(min + ((max - min) * i) / (BAND_SAMPLE_POINTS - 1));
    }
    // A hair below AND above each extra point, so a cutoff landing
    // exactly on it (`>`, `>=`, `<`, `<=` all differ on which side owns
    // the boundary value itself) is seen correctly from both sides --
    // confirmed necessary: probing only the low side left a real gap
    // between a `>` cutoff's two neighbouring bands (57.00 to 57.17 for
    // Aortic Stenosis Risk Score) instead of them meeting exactly at 57.
    const extras = extraPoints.filter((t) => t > min && t < max).flatMap((t) => [t - 1e-6, t, t + 1e-6]);
    sampleValues = [...new Set([...base, ...extras])].sort((a, b) => a - b);
  }

  // The interpretation's real output at one value of the score (null when
  // not visible or not a usable meaning), evaluating only the rows up to
  // it, and memoised -- the probe, the sweep and the bisection below all
  // ask overlapping questions.
  const cache = new Map<number, { text: string; textFa: string } | null>();
  const meaningAt = (v: number) => {
    if (cache.has(v)) return cache.get(v)!;
    const row = computeCalculator(questions, results, answers, {
      overrides: { [targetPosition]: v },
      stopAfter: meaningPosition,
      stringsFa,
    })
      .find((c) => c.position === meaningPosition);
    const out = row && row.visible && row.answerText !== null && isUsableMeaning(row.answerText)
      ? { text: row.answerText, textFa: row.answerTextFa ?? row.answerText }
      : null;
    cache.set(v, out);
    return out;
  };

  // A cheap spread-out probe first: a row that never yields a usable
  // meaning (a bare number everywhere) is dismissed without a full sweep,
  // and whether this row prints the score back (see echoKey) is settled
  // here so the sweep can group as it goes.
  const stride = Math.max(1, Math.floor(sampleValues.length / 16));
  const probeValues = new Set<number>([sampleValues[sampleValues.length - 1]]);
  for (let i = 0; i < sampleValues.length; i += stride) probeValues.add(sampleValues[i]);
  const probes = [...probeValues].flatMap((v) => {
    const m = meaningAt(v);
    return m ? [{ v, text: m.text }] : [];
  });
  if (probes.length === 0) return [];
  const echoes = probes.filter((p) => echoKey(p.text, p.v) !== null).length >= probes.length * 0.9;
  const keyOf = (text: string, v: number) => (echoes ? echoKey(text, v) ?? text : text);

  // The full sweep, grouped as it goes -- abandoned the moment it passes
  // MAX_SENSIBLE_BANDS, so a hundreds-rung ladder (CDC's 0.01-step
  // percentile table) costs ~20 evaluations, not all of them.
  const groups: { key: string; from: number; to: number; text: string; textFa: string }[] = [];
  for (const v of sampleValues) {
    const m = meaningAt(v);
    if (!m) continue;
    const key = keyOf(m.text, v);
    const last = groups[groups.length - 1];
    if (last && last.key === key) {
      last.to = v;
      continue;
    }
    if (groups.length >= MAX_SENSIBLE_BANDS) return [];
    groups.push({
      key,
      from: v,
      to: v,
      text: echoes ? stripEcho(m.text, v) : m.text,
      textFa: echoes ? stripEcho(m.textFa, v) : m.textFa,
    });
  }
  if (groups.length < 2) return [];

  // A boundary within a hair of a known threshold (inserted above) IS
  // that threshold, exactly -- display the clean number, not whatever
  // float arithmetic landed on.
  for (const g of groups) {
    for (const t of extraPoints) {
      if (Math.abs(g.from - t) < 1e-3) g.from = t;
      if (Math.abs(g.to - t) < 1e-3) g.to = t;
    }
  }

  // Neighbouring tiers are sampled at separate values, so a gap remains
  // between the last value of one and the first of the next (CDC: -1.65 |
  // -1.48; Edinburgh: 9 | 10). Where the true cutoff lies:
  //  1. a cutoff written in the formula inside the gap -- both tiers meet
  //     exactly there (-1.64);
  //  2. otherwise bisect on the formula itself until its answer flips,
  //     which finds the exact cutoff however the formula expresses it --
  //     a derived value (SNAP-IV compares `$result0 / 9 > 2.56`, so 23.04
  //     on the score; TEVAR compares `exp($result0) * 100 > 4`), a
  //     parenthesised token, anything. Never a guess: if a midpoint gives
  //     neither tier's answer (an integer `==` chain falling through at
  //     0.5), there's no continuous cutoff to find and the gap is left as
  //     the honest step between two values the score can take.
  const keyAt = (v: number): string | null => {
    const m = meaningAt(v);
    return m ? keyOf(m.text, v) : null;
  };
  const sortedCuts = [...new Set(extraPoints)].sort((a, b) => a - b);
  for (let i = 0; i < groups.length - 1; i++) {
    const lower = groups[i];
    const upper = groups[i + 1];
    if (upper.from - lower.to <= 1e-9) continue;
    const cut = sortedCuts.find((t) => t >= lower.to - 1e-9 && t <= upper.from + 1e-9);
    if (cut !== undefined) {
      lower.to = cut;
      upper.from = cut;
      continue;
    }
    let lo = lower.to;
    let hi = upper.from;
    let flips = true;
    for (let step = 0; step < 60 && hi - lo > 1e-9; step++) {
      const mid = (lo + hi) / 2;
      const key = keyAt(mid);
      if (key === lower.key) lo = mid;
      else if (key === upper.key) hi = mid;
      else {
        flips = false;
        break;
      }
    }
    if (flips) {
      const edge = Number(hi.toPrecision(10));
      lower.to = edge;
      upper.from = edge;
    }
  }

  const bands: ScoreBand[] = groups.map(({ from, to, text, textFa }) => ({ from, to, text, textFa }));
  // The sample grid's own endpoints already equal min/max exactly -- this
  // just guards float drift so the drawn arc has no visible gap at either
  // end.
  bands[0].from = min;
  bands[bands.length - 1].to = max;
  return bands;
}

type Scale = { min: number; max: number; minOpen: boolean; maxOpen: boolean };

/** The span a gauge is drawn over, three honest cases:
 *
 * - Percentage (isPercentageResult): 0 to 100, the real bound of a
 *   probability, both ends closed.
 * - Every input this result reads is bounded: the swept achievable
 *   `[min, max]` IS the calculator's exact scale (every combination it
 *   allows), both ends closed. A cutoff outside it marks a tier the
 *   calculator can't actually reach for anyone, so that tier isn't drawn.
 * - The result reads a question with no real limit (open): the achievable
 *   range is only THIS patient's slice -- their age or lab value pinned --
 *   and is not the scale at all (confirmed wrong both ways: ASDAS-CRP's
 *   slice started exactly at its 1.3 cutoff, hiding its whole "Inactive"
 *   tier; BMI's slice was a single point, so no gauge appeared at all).
 *   The scale is then the dependent row's own cutoffs, with drawing room
 *   past the outermost ones so the open-ended tiers are visible, and both
 *   ends flagged open: that room is geometry, never a number shown to the
 *   user (the gauge labels an open end with its cutoff as an inequality).
 *   Null when there are no cutoffs to anchor it -- nothing honest to draw. */
function resolveScale(
  value: number,
  achieved: MinMax | null,
  cuts: number[],
  percentage: boolean,
  open: boolean,
): Scale | null {
  if (percentage) {
    return {
      min: Math.min(0, value, achieved?.min ?? 0),
      max: Math.max(100, value, achieved?.max ?? 100),
      minOpen: false,
      maxOpen: false,
    };
  }
  if (!open) {
    if (!achieved || !(achieved.min < achieved.max)) return null;
    return { min: achieved.min, max: achieved.max, minOpen: false, maxOpen: false };
  }
  const sorted = [...new Set(cuts)].sort((a, b) => a - b);
  if (sorted.length === 0) return null;
  const low = sorted[0];
  const high = sorted[sorted.length - 1];
  const room = high > low ? (high - low) * 0.25 : Math.max(Math.abs(low) * 0.5, 1);
  let min = Math.min(low - room, value - room * 0.15);
  let max = Math.max(high + room, value + room * 0.15);
  // An integer score with integer cutoffs stays whole, so the tier sweep
  // samples only values it can really take (see computeTierBands).
  if (isWholeNumber(value) && sorted.every(isWholeNumber)) {
    min = Math.floor(min);
    max = Math.ceil(max);
  }
  return { min, max, minOpen: true, maxOpen: true };
}

/** A result templated as a literal percentage of ITS OWN value
 * ("$result0%" where this is result 0's own answer) has an exact,
 * universal scale to show regardless of any one patient's achievable
 * slice or any threshold the dependent row happens to define: 0 to 100,
 * the real mathematical range of a probability -- not an approximation,
 * not padding, the actual bound. Requires the `%` to sit right after
 * this row's own `$result<position>` token, not just anywhere in the
 * template -- a descriptive answer can mention an unrelated percentage
 * in running text (confirmed real: "AR: Quantification"'s grading text
 * reads "...Jet width <25% LV outflow tract..." with no `$result` token
 * at all, nothing to do with this row's own scale) and must not be
 * mistaken for one. Checked on the TARGET result's own template, never
 * the dependent row's -- a dependent row's bucket text ("2.8 %") says
 * nothing about the target's own scale either. */
function isPercentageResult(row: CalculatorResultDef | undefined, targetPosition: number): boolean {
  if (!row) return false;
  const pattern = new RegExp(`\\$result${targetPosition}(?!\\d)\\s*%`);
  return pattern.test(row.answer ?? "") || pattern.test(row.answer_fa ?? "");
}

/** How many different risk levels a set of bands spells out in its own
 * words (classifyResultTone; no tone word counts as one level) -- an
 * interpretation that says "Low / Intermediate / High risk" is the one
 * the gauge exists for, over another row of the same calculator that's a
 * disposition ("Consider admission") or a value table, even when that
 * other row has fewer tiers (confirmed: EHMRG's 2-tier recommendation row
 * beat its 5-tier risk grade on tier count alone). */
function toneVariety(bands: ScoreBand[]): number {
  return new Set(bands.map((b) => classifyResultTone(b.text) ?? "none")).size;
}

function referencesResult(row: CalculatorResultDef, targetPosition: number): boolean {
  const re = new RegExp(`\\$result${targetPosition}(?![\\w$])`);
  return re.test(row.formula ?? "") || re.test(row.condition_formula ?? "");
}

/** The gauge for one numeric result: tries EVERY other row that reads it
 * back as its interpretation and keeps the one that spells out the most
 * risk levels (toneVariety), then the fewest real tiers (at least two) --
 * a classification ("Low / Moderate / High risk") over a fine-grained
 * ladder of the same scale ("2.0%, 2.4%, 2.8%, ...") or a value printed
 * in a sentence.
 * Replaces taking the first such row that happened to return text for
 * this patient's answers, which picked wrong or nothing in real data:
 * Framingham 2008 and ECABG got their 20+-rung % ladder (dropped as too
 * many tiers) instead of their Low/Moderate/High row; SNAP-IV's ODD score
 * got the ADHD row because its own row wasn't visible at that patient's
 * answers; Brain Metastases' "3 / 5.5 / 9.4 / 14.8 Months" tiers were
 * skipped for returning numbers. No tiered row at all: a plain neutral
 * arc over a real closed scale, or no gauge when the scale is open (there
 * would be no honest number for either end). */
function resolveRange(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  target: CalculatorResultDef,
  value: number,
  achieved: MinMax | null,
  open: boolean,
  reachable: number[] | null,
  stringsFa?: Record<string, string>,
): ResultRange | null {
  const percentage = isPercentageResult(target, target.position);
  let best: { range: ResultRange; variety: number } | null = null;
  for (const candidate of [...results].sort((a, b) => a.position - b.position)) {
    if (candidate.position === target.position || !referencesResult(candidate, target.position)) continue;
    const cuts = [
      ...extractThresholds(candidate.formula ?? "", target.position),
      ...extractThresholds(candidate.condition_formula ?? "", target.position),
    ];
    const scale = resolveScale(value, achieved, cuts, percentage, open);
    if (!scale) continue;
    // Only a closed, non-percentage scale IS exactly its reachable set; a
    // percentage's 0-100 and an open scale's drawing room reach past it.
    const exact = !percentage && !scale.minOpen && !scale.maxOpen ? reachable : null;
    const bands = computeTierBands(
      questions, results, answers, target.position, candidate.position, scale.min, scale.max, cuts, percentage, exact,
      stringsFa,
    );
    if (bands.length < 2) continue;
    const variety = toneVariety(bands);
    if (
      !best
      || variety > best.variety
      || (variety === best.variety && bands.length < best.range.bands.length)
    ) {
      best = { range: { ...scale, bands }, variety };
    }
  }
  if (best) return best.range;

  const plain = resolveScale(value, achieved, [], percentage, open);
  return plain && !plain.minOpen && !plain.maxOpen ? { ...plain, bands: [] } : null;
}

/** The gauge scale (and meaning bands) for every numeric result, given
 * the learner's own answers -- a question with no real bound is pinned to
 * whatever they actually entered for it rather than blocking every
 * result's range (see questionDomain), and a result that depends on such
 * a question gets an open scale (see resolveScale). `answers` must have a
 * value for every question (the caller only calls this after full
 * validation). `stringsFa` is the calculator's `formula_strings_fa`, so
 * the bands' Persian labels are real translations. */
export function computeResultRanges(
  questions: CalculatorQuestion[],
  results: CalculatorResultDef[],
  answers: CalculatorAnswers,
  stringsFa?: Record<string, string>,
): Map<number, ResultRange> {
  const domains = questions.map((q) => ({ position: q.position, domain: questionDomain(q, answers) }));
  if (domains.length === 0 || domains.some((d) => d.domain === null)) return new Map();
  const bounded: Domain[] = domains.map((d) => ({ position: d.position, values: d.domain!.values }));
  const pinned = domains.filter((d) => d.domain!.pinned).map((d) => d.position);

  let combinationCount = 1;
  for (const d of bounded) combinationCount *= d.values.length;
  if (combinationCount === 0) return new Map();

  let achieved: Map<number, MinMax>;
  const reachableSets = new Map<number, Set<number> | null>();
  if (combinationCount > MAX_RANGE_COMBINATIONS) {
    achieved = heuristicResultRanges(questions, results, bounded);
  } else {
    achieved = new Map();
    sweepCombinations(cartesian(bounded), questions, results, achieved, reachableSets);
  }

  // The swept values are a result's complete reachable set only when every
  // input is a choice (or fixed) -- a bounded numeric input is sampled on
  // a grid, so a score it feeds can also land between those samples (the
  // CDC z-scores did, and their tier edges came out at sampled values,
  // not the formula's cutoffs).
  const discrete = questions.every(
    (q, i) => q.type === "multiple_choice" || domains[i].domain!.values.length === 1,
  );

  const actual = computeCalculator(questions, results, answers);
  const ranges = new Map<number, ResultRange>();
  for (const target of results) {
    const c = actual.find((x) => x.position === target.position);
    if (!c || !c.visible || c.answerText === null) continue;
    const value = extractNumericValue(c.answerText);
    if (value === null) continue;
    const open = pinned.some((p) => dependsOnQuestion(questions, results, answers, target.position, p, value));
    const seen = discrete ? reachableSets.get(target.position) : null;
    const reachable = seen ? [...seen].sort((a, b) => a - b) : null;
    const range = resolveRange(
      questions, results, answers, target, value, achieved.get(target.position) ?? null, open, reachable, stringsFa,
    );
    if (range) ranges.set(target.position, range);
  }
  return ranges;
}
