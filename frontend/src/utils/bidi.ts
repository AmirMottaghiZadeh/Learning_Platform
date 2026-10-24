/**
 * The presentation layer between Persian text from the database and the
 * screen: a Persian sentence is laid out right-to-left, with every English
 * stretch in it (a drug or brand name, a unit, a code -- "mg/kg/day",
 * "CYP3A4", "QTc") isolated as its own left-to-right run.
 *
 * Without it the layout guessed each paragraph's direction from its first
 * strong letter (Android always; the web too, through `dir="auto"`), so a
 * Persian sentence that opened with an English word was laid out
 * left-to-right; and the punctuation, brackets and numbers next to an
 * English word took that word's direction, which scrambled the sentence
 * around it.
 *
 * Done with Unicode's own controls, which every platform's text layout
 * honours (no extra elements, so it works in a single Text node on native):
 * - RLM (U+200F) opens every line: a strong right-to-left mark, so the
 *   line's base direction is right-to-left whatever letter follows;
 * - LRI (U+2066) ... PDI (U+2069) around each English run: an isolate,
 *   laid out left-to-right inside and seen as one neutral unit outside.
 * The text itself is not changed -- the controls are invisible -- and the
 * database keeps the plain text: this runs only when the text is drawn.
 */

export const RLM = "\u200F";
export const LRI = "\u2066";
export const PDI = "\u2069";

/** A Persian (Arabic-script) letter -- not a Persian digit, which carries
 * no direction of its own. */
const PERSIAN_LETTER = /[\u0620-\u064A\u066E-\u06D3\u06D5\u06EE\u06EF\u06FA-\u06FF]/;

// One English token: it starts with a Latin or Greek letter, a Latin digit
// or µ, may hold the symbols units and codes are written with, and ends on a
// letter, digit, superscript, %, °, + or ' -- never on the sentence's own
// punctuation («... mg/day.»: the full stop belongs to the Persian sentence).
const TOKEN_START = "A-Za-z0-9\u00B5\u0391-\u03A9\u03B1-\u03C9";
const TOKEN_BODY = `${TOKEN_START}\u00B2\u00B3\u00B9\u2070-\u2079\u00B0%+\\-/.,\u00B7\u00D7^'\u2019_:#&=~`;
const TOKEN_END = `${TOKEN_START}\u00B2\u00B3\u00B9\u2070-\u2079\u00B0%+'\u2019`;
const TOKEN = `[${TOKEN_START}](?:[${TOKEN_BODY}]*[${TOKEN_END}])?`;
// Tokens one space apart are one run ("Pneumocystis jirovecii", "10 mg").
const ENGLISH_RUN = new RegExp(`${TOKEN}(?:[ \u00A0]+${TOKEN})*`, "g");

// A number and the unit after it stay on one line («87.5 mg», never «87.5»
// at the end of one line and «mg» at the start of the next).
const NUMBER_THEN_UNIT = /([0-9]) (?=[A-Za-z\u00B5])/g;

export function hasPersianLetters(text: string): boolean {
  return PERSIAN_LETTER.test(text);
}

/** `text` -- a piece of a Persian paragraph -- with each English run
 * isolated and each line opened with an RLM. Running it twice changes
 * nothing more. */
export function isolateEnglish(text: string): string {
  if (!text || text.includes(LRI)) return text;
  const isolated = text.replace(ENGLISH_RUN, (run) => LRI + run.replace(NUMBER_THEN_UNIT, "$1\u00A0") + PDI);
  return RLM + isolated.replace(/\n/g, `\n${RLM}`);
}
