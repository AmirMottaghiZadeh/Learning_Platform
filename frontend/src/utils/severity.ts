/**
 * How serious a tier of a result is -- "Low risk", "Moderate", "Severe" --
 * as a level from 0 (nothing to worry about) to 3 (act on it), so every
 * ordinal result can be coloured the same way.
 *
 * The words of the tier decide where they say something ("high", "mild",
 * "unlikely"). A tier with no such word takes its place on the calculator's
 * own ladder, spread evenly from 0 for the lowest to 3 for the highest, which
 * assumes what nearly every score does: a higher number is worse.
 */

export type Severity = 0 | 1 | 2 | 3;

const NEGATED = /\b(?:not|no|non|without|never|does not|do not|doesn't)\s+(?:\w+\s+){0,3}?(?:high|severe|severely|likely|probable|positive|definite|required|indicated|consistent|meet|meets|present|elevated|abnormal|criteria)/;

export function severityOfText(raw: string): Severity | null {
  const text = raw.toLowerCase().replace(/<[^>]+>/g, " ");
  if (/\bnot\s+(?:low|normal|minimal)\b/.test(text)) return 2;
  if (/\blow[\s-]+intermediate\b/.test(text)) return 1;
  if (NEGATED.test(text) || /\b(?:unlikely|ruled out|rule out|not likely)\b/.test(text)) return 0;
  if (/\b(?:very high|high|severe|severely|critical|extreme|definite|overt|impending|emergen\w+|positive|dependen\w+|failure|poor|unstable|urgent|abnormal|malignant)\b/.test(text)) return 3;
  if (/\b(?:moderate|moderately|medium|intermediate|elevated|borderline|possible|probable|likely|suspected|increased|consistent with|meets?|obes\w+)\b/.test(text)) return 2;
  if (/\b(?:mild|mildly|slight|minor|early|underweight|overweight)\b/.test(text)) return 1;
  if (/\b(?:minimal|minimum|none|low|very low|normal|negative|absent|healthy|good|excellent|stable|inactive|remission)\b/.test(text)) return 0;
  return null;
}

/** A level for each tier of a ladder given lowest-first. */
export function severityLevels(texts: string[]): Severity[] {
  const last = Math.max(texts.length - 1, 1);
  return texts.map((text, i) => {
    const byWords = severityOfText(text);
    if (byWords !== null) return byWords;
    return Math.round((i * 3) / last) as Severity;
  });
}
