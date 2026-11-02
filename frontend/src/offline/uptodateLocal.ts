import type { SearchPageArgs } from "@/api/endpoints";
import type { UptodateArticle, UptodateImage, UptodateSearchPage, UptodateSearchResult } from "@/api/types";

import type { Locator, PackageReader } from "./reader";

/** UpToDate answered from the installed package, in the API's own shapes.
 * The search mirrors apps/uptodate/services.py's title search line for line
 * -- the same matches, corrections and order; articles and images as stored. */

type UptodateIndex = {
  version: string;
  sections: string[];
  topics: {
    ids: string[];
    titles: string[];
    sections: number[];
    updated: string[];
  };
  articles: { ids: string[]; locs: number[] };
  images: { ids: string[]; types: string[]; locs: number[] };
};

/** The server's `TitleIndex`. */
type TitleIndex = {
  words: string[][];
  /** every distinct title word, sorted, and the titles that have it */
  vocab: string[];
  postings: Map<string, number[]>;
  /** each vocab word's letters (`letters`) */
  letters: number[];
};

type Term = [term: string, whole: string, corrected: boolean];

type Prepared = {
  index: UptodateIndex;
  titles: TitleIndex;
  terms: Map<string, Term>;
  infixes: Map<string, string[]>;
  articleAt: Map<string, number>;
  imageAt: Map<string, number>;
};

const cache = new Map<string, Promise<Prepared>>();

function prepared(reader: PackageReader): Promise<Prepared> {
  const build = reader.manifest.build;
  let entry = cache.get(build);
  if (!entry) {
    entry = reader.index<UptodateIndex>().then((index) => ({
      index,
      titles: buildTitleIndex(index.topics.titles),
      terms: new Map(),
      infixes: new Map(),
      articleAt: new Map(index.articles.ids.map((id, i) => [id, i])),
      imageAt: new Map(index.images.ids.map((id, i) => [id, i])),
    }));
    cache.clear(); // one build at a time
    cache.set(build, entry);
    entry.catch(() => cache.delete(build));
  }
  return entry;
}

const loc = (locs: number[], i: number): Locator => [locs[i * 3], locs[i * 3 + 1], locs[i * 3 + 2]];

/** The server's `_search_words`. */
export function searchWords(raw: string): string[] {
  return (raw.match(/[A-Za-z0-9\u0600-\u06FF]+/g) ?? []).slice(0, 8);
}

// ---- Title search: services.py's, step by step ----

const TITLE_WORD_RE = /[a-z0-9]+/g;
const TAG_RE = /<[^>]*>/g;

export function titleWords(title: string): string[] {
  // some titles italicise a name: "<i>Chlamydia pneumoniae</i>"
  return (title || "").replace(TAG_RE, " ").toLowerCase().match(TITLE_WORD_RE) ?? [];
}

export function buildTitleIndex(titles: string[]): TitleIndex {
  const words = titles.map(titleWords);
  const postings = new Map<string, number[]>();
  words.forEach((title, i) => {
    for (const word of new Set(title)) {
      const list = postings.get(word);
      if (list) list.push(i);
      else postings.set(word, [i]);
    }
  });
  const vocab = [...postings.keys()].sort();
  return { words, vocab, postings, letters: vocab.map(letters) };
}

/** The set of characters in `word`, as bits (a lower bound only, so the
 * bits need not be the server's). */
function letters(word: string): number {
  let bits = 0;
  for (let k = 0; k < word.length; k++) bits |= 1 << (word.charCodeAt(k) % 31);
  return bits;
}

function bitCount(n: number): number {
  let count = 0;
  for (let v = n >>> 0; v; v &= v - 1) count++;
  return count;
}

function lowerBound(vocab: string[], word: string): number {
  let low = 0;
  let high = vocab.length;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (vocab[mid] < word) low = mid + 1;
    else high = mid;
  }
  return low;
}

/** The title words that start with `prefix`. */
function prefixed(vocab: string[], prefix: string): string[] {
  const start = lowerBound(vocab, prefix);
  let end = start;
  while (end < vocab.length && vocab[end].startsWith(prefix)) end++;
  return vocab.slice(start, end);
}

function isWord(vocab: string[], word: string): boolean {
  const i = lowerBound(vocab, word);
  return i < vocab.length && vocab[i] === word;
}

function maxTypos(length: number, prefix: boolean): number {
  // a word still being typed gets fewer: its starts are many
  return length <= 4 ? 1 : length <= 8 || prefix ? 2 : 3;
}

/** Edits (insert, delete, substitute, swap two neighbours) from `word` to
 * `candidate` -- or, with `prefix`, to the closest start of it -- as
 * [distance, length of that start]; null past `limit`. */
export function typoDistance(word: string, candidate: string, limit: number, prefix: boolean): [number, number] | null {
  const m = word.length;
  const n = prefix ? Math.min(candidate.length, m + limit) : candidate.length;
  if (n < m - limit || n > m + limit) return null;
  const over = limit + 1;
  // only cells within `limit` of the diagonal can stay within `limit`
  let before: number[] | null = null;
  let row = Array.from({ length: n + 1 }, (_, j) => (j <= limit ? j : over));
  for (let i = 1; i <= m; i++) {
    const current: number[] = new Array(n + 1).fill(over);
    if (i <= limit) current[0] = i;
    const low = Math.max(1, i - limit);
    const high = Math.min(n, i + limit);
    const letter = word[i - 1];
    let least = current[low - 1];
    for (let j = low; j <= high; j++) {
      const other = candidate[j - 1];
      let value = row[j - 1] + (letter !== other ? 1 : 0);
      if (row[j] + 1 < value) value = row[j] + 1;
      if (current[j - 1] + 1 < value) value = current[j - 1] + 1;
      if (before && j > 1 && letter === candidate[j - 2] && word[i - 2] === other && before[j - 2] + 1 < value) {
        value = before[j - 2] + 1;
      }
      current[j] = value < over ? value : over;
      if (current[j] < least) least = current[j];
    }
    if (least > limit) return null;
    before = row;
    row = current;
  }
  if (!prefix) return row[n] <= limit ? [row[n], n] : null;
  // the closest start, at least as long as the word less its typos; a tie
  // goes to the longer start (the whole word, when it fits)
  let best: [number, number] | null = null;
  for (let j = Math.max(1, m - limit); j <= n; j++) {
    if (row[j] <= limit && (best === null || row[j] <= best[0])) best = [row[j], j];
  }
  return best;
}

function compareKeys(a: (number | string | boolean)[], b: (number | string | boolean)[]): number {
  for (let k = 0; k < a.length; k++) {
    if (a[k] < b[k]) return -1;
    if (a[k] > b[k]) return 1;
  }
  return 0;
}

/** The title word -- or a word's start, for a word still being typed --
 * closest to a misspelt `word`. */
function nearest(word: string, index: TitleIndex): string | null {
  // a short word is only compared to whole words: its starts are too many
  const prefix = word.length >= 5;
  const wholeLimit = maxTypos(word.length, false);
  const prefixLimit = maxTypos(word.length, prefix);
  const mine = letters(word);
  let bestKey: (number | string | boolean)[] | null = null;
  let best: string | null = null;
  index.vocab.forEach((candidate, k) => {
    const theirs = index.letters[k];
    // each of the word's letters the candidate lacks costs an edit, and so
    // does each of the candidate's the word lacks: a quick lower bound
    const lacking = bitCount(mine & ~theirs);
    if (lacking > wholeLimit) return;
    let found: [number, number] | null = null;
    if (Math.max(lacking, bitCount(theirs & ~mine)) <= wholeLimit) found = typoDistance(word, candidate, wholeLimit, false);
    if (prefix && lacking <= prefixLimit) {
      const start = typoDistance(word, candidate, prefixLimit, true);
      if (start && (found === null || start[0] < found[0])) found = start;
    }
    if (!found) return;
    const [distance, length] = found;
    const whole = length === candidate.length;
    // fewest typos, then a whole word, then the word most titles share
    const key = [distance, !whole, -index.postings.get(candidate)!.length, candidate];
    if (bestKey === null || compareKeys(key, bestKey) < 0) {
      bestKey = key;
      best = candidate.slice(0, length);
    }
  });
  return best;
}

/** A word this long is also found inside title words: "kalemia" finds
 * "hyperkalemia", "tension" "hypertension". Shorter ones would find too much. */
const MIN_INFIX = 4;

/** The title words that have `term` inside them, not at their start. */
function infixed(prep: Prepared, term: string): string[] {
  if (term.length < MIN_INFIX) return [];
  let found = prep.infixes.get(term);
  if (!found) {
    found = prep.titles.vocab.filter((w) => w.includes(term) && !w.startsWith(term));
    prep.infixes.set(term, found);
  }
  return found;
}

/** How one query word is matched: the start (or, from MIN_INFIX letters, a
 * part) of title words it must be, the whole word it stands for, and
 * whether that is a spelling correction. */
function term(word: string, prep: Prepared): Term {
  const index = prep.titles;
  const whole = word.toLowerCase();
  if (whole.length < 3 || prefixed(index.vocab, whole).length || infixed(prep, whole).length) {
    // a plural also finds the singular ("infections" -> "infection")
    const singular = whole.slice(0, -1);
    if (whole.length >= 6 && whole.endsWith("s") && isWord(index.vocab, singular)) return [singular, whole, false];
    return [whole, whole, false];
  }
  const near = nearest(whole, index);
  return near ? [near, near, true] : [whole, whole, false];
}

/** Words that say little about what a topic is about: a title made of the
 * query and these is the general topic ("Overview of hypertension in
 * adults"), ahead of the narrower ones ("Hypertension in athletes"). */
const GENERAL_WORDS = new Set(
  "a an and the of in on for to with by or at from its overview introduction adult adults child children".split(" "),
);
/** Topics that serve another reader or only list links: after the reviews. */
const SECONDARY_STARTS = ["patient education", "society guideline"];

function rank(index: TitleIndex, titles: string[], i: number, matched: Term[]): (number | string | boolean)[] {
  const words = index.words[i];
  const terms = matched.map(([t]) => t);
  let first = words.findIndex((word) => terms.some((t) => word.startsWith(t)));
  if (first < 0) first = words.length;
  // a term found only inside words ("tension" in "hypertension")
  const inside = terms.filter((t) => !words.some((word) => word.startsWith(t))).length;
  const whole = matched.filter(([t, w]) => words.includes(t) || words.includes(w)).length;
  const secondary = SECONDARY_STARTS.includes(words.slice(0, 2).join(" "));
  const overview = words.includes("overview");
  const extra = words.filter((word) => !GENERAL_WORDS.has(word) && !terms.some((t) => word.includes(t))).length;
  const exact = words.join(" ") === matched.map(([, w]) => w).join(" ") && words.length === matched.length;
  // the title that is the query; then every word at a word's start, whole
  // words over starts; reviews before patient pages and link lists; an
  // overview first; the general topic (fewest other words) before the
  // narrow; the word early in the title; shorter titles
  return [!exact, inside, -whole, secondary, !overview, extra, first, words.length, titles[i].toLowerCase(), i];
}

/** services.search_page: every topic whose title has every query word, best
 * first, one page of them, with every match counted per section. */
export async function searchTopicsPage(
  reader: PackageReader,
  query: string,
  { limit = 30, offset = 0, section = "" }: SearchPageArgs = {},
): Promise<UptodateSearchPage> {
  const empty: UptodateSearchPage = { total: 0, all: 0, sections: [], terms: [], corrected: "", results: [] };
  const words = searchWords(query);
  if (!words.length) return empty;
  const prep = await prepared(reader);
  const { index, titles: titleIndex } = prep;

  const matched = words.map((word) => {
    const key = word.toLowerCase();
    let found = prep.terms.get(key);
    if (!found) {
      found = term(word, prep);
      prep.terms.set(key, found);
    }
    return found;
  });
  const terms = [...new Set(matched.map(([t]) => t))];
  const corrected = matched.some(([, , fix]) => fix) ? matched.map(([, w]) => w).join(" ") : "";

  // the titles with every term (`terms` is never empty)
  let found: number[] = [];
  terms.forEach((t, k) => {
    const having = new Set<number>();
    for (const word of [...prefixed(titleIndex.vocab, t), ...infixed(prep, t)]) {
      for (const i of titleIndex.postings.get(word)!) having.add(i);
    }
    found = k === 0 ? [...having] : found.filter((i) => having.has(i));
  });
  if (!found.length) return { ...empty, terms, corrected };
  const { topics, sections } = index;
  const keys = new Map(found.map((i) => [i, rank(titleIndex, topics.titles, i, matched)]));
  let ranked = found.sort((a, b) => compareKeys(keys.get(a)!, keys.get(b)!));
  const sectionOf = (i: number) => sections[topics.sections[i]] ?? "";

  const counts = new Map<string, number>();
  for (const i of ranked) {
    const name = sectionOf(i);
    if (name) counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  const all = ranked.length;
  if (section) ranked = ranked.filter((i) => sectionOf(i) === section);
  const page = ranked.slice(Math.max(0, offset), Math.max(0, offset) + Math.max(0, limit));

  return {
    total: ranked.length,
    all,
    sections: [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
      .map(([name, count]) => ({ name, count })),
    terms,
    corrected,
    results: page.map((i) => ({
      id: topics.ids[i],
      title: topics.titles[i],
      section: sectionOf(i),
      version: index.version,
      snippet: "",
      updated: topics.updated[i] ?? "",
      terms,
      corrected,
    })),
  };
}

export async function searchTopics(reader: PackageReader, query: string, limit = 25): Promise<UptodateSearchResult[]> {
  return (await searchTopicsPage(reader, query, { limit })).results;
}

/** null when the package has no such article. */
export async function getTopic(reader: PackageReader, id: string): Promise<UptodateArticle | null> {
  const { index, articleAt } = await prepared(reader);
  const i = articleAt.get(String(id));
  return i === undefined ? null : reader.json<UptodateArticle>(loc(index.articles.locs, i));
}

const IMAGE_TYPES = new Set(["png", "jpeg", "gif", "webp"]);

export async function getImage(reader: PackageReader, id: string): Promise<UptodateImage | null> {
  const { index, imageAt } = await prepared(reader);
  const i = imageAt.get(String(id));
  if (i === undefined) return null;
  const type = index.images.types[i];
  return {
    id: String(id),
    content_type: IMAGE_TYPES.has(type) ? `image/${type}` : "image/jpeg",
    data_base64: await reader.base64(loc(index.images.locs, i)),
  };
}

export function forgetUptodate() {
  cache.clear();
}
