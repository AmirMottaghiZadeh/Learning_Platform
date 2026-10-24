import type { UptodateArticle, UptodateImage, UptodateSearchResult } from "@/api/types";

import { queryTerm } from "./porter";
import type { Locator, PackageReader } from "./reader";

/** UpToDate answered from the installed package, in the API's own shapes.
 * Mirrors apps/uptodate/services.py: title search ranked like FTS5's bm25,
 * the snippet cut the way `_snippet` cuts it, articles and images as stored. */

type UptodateIndex = {
  version: string;
  sections: string[];
  topics: {
    ids: string[];
    titles: string[];
    sections: number[];
    updated: string[];
    heads: number[];
    /** each title's porter terms, space-separated */
    terms: string[];
    /** tokens in the topic's FTS row (title + text), for bm25 */
    lengths: number[];
  };
  rows: number;
  avg_length: number;
  articles: { ids: string[]; locs: number[] };
  images: { ids: string[]; types: string[]; locs: number[] };
};

type Prepared = {
  index: UptodateIndex;
  terms: string[][];
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
      terms: index.topics.terms.map((t) => (t ? t.split(" ") : [])),
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
  return (raw.match(/[A-Za-z0-9؀-ۿ]+/g) ?? []).slice(0, 8);
}

// FTS5's bm25 constants.
const K1 = 1.2;
const B = 0.75;

const SNIPPET_RADIUS = 110;

/** `_snippet`'s windowing over a topic's stored snippet source. */
export function cutSnippet(text: string, words: string[]): string {
  if (!text) return "";
  const lowered = text.toLowerCase();
  const phrase = words.join(" ").toLowerCase();
  let hit = phrase ? lowered.indexOf(phrase) : -1;
  if (hit < 0) {
    const hits = words.map((w) => lowered.indexOf(w.toLowerCase())).filter((i) => i >= 0);
    hit = hits.length ? Math.min(...hits) : -1;
  }
  let start: number;
  let end: number;
  if (hit < 0) {
    start = 0;
    end = SNIPPET_RADIUS * 2;
  } else {
    start = Math.max(0, hit - SNIPPET_RADIUS);
    end = hit + SNIPPET_RADIUS;
  }
  if (start > 0) {
    const space = text.indexOf(" ", start);
    start = space >= 0 && space < hit ? space + 1 : start;
  }
  if (end < text.length) {
    const space = text.lastIndexOf(" ", end - 1);
    end = space > start ? space : end;
  }
  const excerpt = text.slice(start, end).trim();
  return (start > 0 ? "…" : "") + excerpt + (end < text.length ? "…" : "");
}

export async function searchTopics(reader: PackageReader, query: string, limit = 25): Promise<UptodateSearchResult[]> {
  const words = searchWords(query);
  if (!words.length) return [];
  const { index, terms } = await prepared(reader);
  const wanted = words.map(queryTerm);

  // Every query word is a prefix phrase on the title column; a topic
  // matches when it has them all.
  const docsWith = wanted.map(() => 0);
  const matches: { i: number; tf: number[] }[] = [];
  for (let i = 0; i < terms.length; i++) {
    const title = terms[i];
    let all = true;
    const tf = wanted.map((w, q) => {
      let n = 0;
      for (const t of title) if (t.startsWith(w)) n++;
      if (n) docsWith[q]++;
      else all = false;
      return n;
    });
    if (all) matches.push({ i, tf });
  }
  if (!matches.length) return [];

  const rows = Math.max(index.rows, terms.length);
  const idf = docsWith.map((n) => {
    const value = Math.log((rows - n + 0.5) / (n + 0.5));
    return value > 0 ? value : 1e-6;
  });
  const avg = index.avg_length || 1;
  const score = ({ i, tf }: { i: number; tf: number[] }) => {
    const norm = K1 * (1 - B + (B * index.topics.lengths[i]) / avg);
    return tf.reduce((sum, f, q) => sum + (idf[q] * f * (K1 + 1)) / (f + norm), 0);
  };
  const ranked = matches
    .map((m) => ({ ...m, s: score(m) }))
    .sort((a, b) => b.s - a.s || a.i - b.i)
    .slice(0, limit);

  const { topics, sections } = index;
  return Promise.all(
    ranked.map(async ({ i }) => ({
      id: topics.ids[i],
      title: topics.titles[i],
      section: sections[topics.sections[i]] ?? "",
      version: index.version,
      snippet: cutSnippet(await reader.text(loc(topics.heads, i)), words),
      updated: topics.updated[i] ?? "",
    })),
  );
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
