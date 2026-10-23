/** The Porter stemmer as SQLite's FTS5 "porter" tokenizer applies it, so a
 * query typed offline stems to the same terms the server's title search
 * looks up. Titles themselves arrive already stemmed (by SQLite, at package
 * build time); only query words go through this. Checked word-for-word
 * against SQLite's own output (see offline/__tests__). */

const isVowelLetter = (c: string) => c === "a" || c === "e" || c === "i" || c === "o" || c === "u";

class Word {
  b: string;
  constructor(b: string) {
    this.b = b;
  }

  /** consonant at i: not a vowel, and a "y" only after a vowel (or first) */
  cons(i: number): boolean {
    const c = this.b[i];
    if (isVowelLetter(c)) return false;
    if (c === "y") return i === 0 ? true : !this.cons(i - 1);
    return true;
  }

  /** m() of the first n letters: the number of vowel-consonant sequences */
  m(n: number): number {
    let i = 0;
    let count = 0;
    while (i < n && this.cons(i)) i++;
    while (i < n) {
      while (i < n && !this.cons(i)) i++;
      if (i >= n) break;
      count++;
      while (i < n && this.cons(i)) i++;
    }
    return count;
  }

  vowelIn(n: number): boolean {
    for (let i = 0; i < n; i++) if (!this.cons(i)) return true;
    return false;
  }

  doubleConsAt(i: number): boolean {
    return i >= 1 && this.b[i] === this.b[i - 1] && this.cons(i);
  }

  /** consonant-vowel-consonant ending at i, the last not w, x or y */
  cvc(i: number): boolean {
    if (i < 2 || !this.cons(i) || this.cons(i - 1) || !this.cons(i - 2)) return false;
    const c = this.b[i];
    return c !== "w" && c !== "x" && c !== "y";
  }

  ends(s: string): boolean {
    // SQLite only matches a suffix that leaves a stem: "ies" alone is not "-ies".
    return this.b.length > s.length && this.b.endsWith(s);
  }

  /** replace suffix `s` by `r` when m() of the stem left is over `min` */
  swap(s: string, r: string, min: number): void {
    const stem = this.b.length - s.length;
    if (this.m(stem) > min) this.b = this.b.slice(0, stem) + r;
  }
}

type Rule = [suffix: string, replacement: string];

/** The first matching suffix wins whether or not its condition holds. */
function firstRule(w: Word, rules: Rule[], min: number): void {
  for (const [s, r] of rules) {
    if (w.ends(s)) {
      w.swap(s, r, min);
      return;
    }
  }
}

const STEP2: Record<string, Rule[]> = {
  a: [["ational", "ate"], ["tional", "tion"]],
  c: [["enci", "ence"], ["anci", "ance"]],
  e: [["izer", "ize"]],
  g: [["logi", "log"]],
  l: [["bli", "ble"], ["alli", "al"], ["entli", "ent"], ["eli", "e"], ["ousli", "ous"]],
  o: [["ization", "ize"], ["ation", "ate"], ["ator", "ate"]],
  s: [["alism", "al"], ["iveness", "ive"], ["fulness", "ful"], ["ousness", "ous"]],
  t: [["aliti", "al"], ["iviti", "ive"], ["biliti", "ble"]],
};

const STEP3: Record<string, Rule[]> = {
  e: [["icate", "ic"], ["ative", ""], ["alize", "al"]],
  i: [["iciti", "ic"]],
  l: [["ical", "ic"], ["ful", ""]],
  s: [["ness", ""]],
};

const STEP4: Record<string, string[]> = {
  a: ["al"],
  c: ["ance", "ence"],
  e: ["er"],
  i: ["ic"],
  l: ["able", "ible"],
  n: ["ant", "ement", "ment", "ent"],
  o: ["ion", "ou"],
  s: ["ism"],
  t: ["ate", "iti"],
  u: ["ous"],
  v: ["ive"],
  z: ["ize"],
};

export function porterStem(token: string): string {
  // SQLite leaves tokens of under 3 or over 64 bytes as they are.
  if (token.length < 3 || token.length > 64) return token;
  const w = new Word(token);

  // Step 1a
  if (w.ends("sses") || w.ends("ies")) w.b = w.b.slice(0, -2);
  else if (w.ends("ss")) {
    /* unchanged */
  } else if (w.ends("s")) w.b = w.b.slice(0, -1);

  // Step 1b
  let step1b2 = false;
  if (w.ends("eed")) {
    if (w.m(w.b.length - 3) > 0) w.b = w.b.slice(0, -1);
  } else if (w.ends("ed") && w.vowelIn(w.b.length - 2)) {
    w.b = w.b.slice(0, -2);
    step1b2 = true;
  } else if (w.ends("ing") && w.vowelIn(w.b.length - 3)) {
    w.b = w.b.slice(0, -3);
    step1b2 = true;
  }
  if (step1b2) {
    if (w.ends("at") || w.ends("bl") || w.ends("iz")) w.b += "e";
    else if (w.doubleConsAt(w.b.length - 1) && !"lsz".includes(w.b[w.b.length - 1])) w.b = w.b.slice(0, -1);
    else if (w.m(w.b.length) === 1 && w.cvc(w.b.length - 1)) w.b += "e";
  }

  // Step 1c
  if (w.ends("y") && w.vowelIn(w.b.length - 1)) w.b = w.b.slice(0, -1) + "i";

  // Steps 2 and 3 (m > 0), 4 (m > 1)
  if (w.b.length > 1) firstRule(w, STEP2[w.b[w.b.length - 2]] ?? [], 0);
  firstRule(w, STEP3[w.b[w.b.length - 1]] ?? [], 0);
  if (w.b.length > 1) {
    for (const s of STEP4[w.b[w.b.length - 2]] ?? []) {
      if (!w.ends(s)) continue;
      const stem = w.b.length - s.length;
      const st = s !== "ion" || (stem > 0 && (w.b[stem - 1] === "s" || w.b[stem - 1] === "t"));
      if (st) {
        if (w.m(stem) > 1) w.b = w.b.slice(0, stem);
        break;
      }
    }
  }

  // Step 5a
  if (w.ends("e")) {
    const a = w.m(w.b.length - 1);
    if (a > 1 || (a === 1 && !w.cvc(w.b.length - 2))) w.b = w.b.slice(0, -1);
  }
  // Step 5b
  if (w.ends("ll") && w.m(w.b.length - 1) > 1) w.b = w.b.slice(0, -1);
  return w.b;
}

/** A query word as FTS5's porter tokenizer reads it: lower-cased, stemmed. */
export function queryTerm(word: string): string {
  return porterStem(word.toLowerCase());
}
