import { stripHtml } from "@/utils/html";
import type { UptodateSearchSuggestion, UptodateSuggestionKind } from "@/api/types";

export type SearchCatalogData = {
  queries: [string, string, number][];
  topics: Record<string, string[]>;
};

export const normalizeSearch = (value: string) =>
  (stripHtml(value).toLowerCase().match(/[a-z0-9\u0600-\u06FF]+/g) ?? []).join(" ");

export function suggestionKind(query: string): UptodateSuggestionKind {
  const word = normalizeSearch(query);
  return /treat|therap|management|regimen/.test(word) ? "treatment"
    : /follow|cure|monitor/.test(word) ? "followup"
      : /diagnos|test|screen|symptom/.test(word) ? "diagnosis" : "general";
}

/** Mirrors backend/apps/uptodate/search_catalog.py, including tie ordering. */
export class SearchCatalog {
  private aliases = new Map<string, [string, number]>();
  private vocab: string[];

  constructor(private data: SearchCatalogData = { queries: [], topics: {} }) {
    for (const [word, concept, weight] of data.queries) {
      const key = normalizeSearch(word);
      const previous = this.aliases.get(key);
      if (key && (!previous || weight > previous[1])) this.aliases.set(key, [String(concept), weight]);
    }
    const explicit = new Set(this.aliases.keys());
    for (const [word, concept, weight] of data.queries) {
      const key = normalizeSearch(word.replace(/\([^)]*\)/g, ""));
      const previous = this.aliases.get(key);
      if (key && !explicit.has(key) && (!previous || weight > previous[1])) this.aliases.set(key, [String(concept), weight]);
    }
    this.vocab = [...this.aliases.keys()].sort();
  }

  resolve(query: string): { concept: string | null; remaining: string[] } {
    const words = normalizeSearch(query).split(" ").filter(Boolean).slice(0, 8);
    for (let length = words.length; length > 0; length--) {
      for (let start = 0; start <= words.length - length; start++) {
        const match = this.aliases.get(words.slice(start, start + length).join(" "));
        if (match) return { concept: match[0], remaining: [...words.slice(0, start), ...words.slice(start + length)] };
      }
    }
    return { concept: null, remaining: words };
  }

  hits(concept: string, query: string): string[] {
    const lists = this.data.topics[concept] ?? [];
    const words = new Set(normalizeSearch(query).split(" "));
    const audience = words.has("patient") && words.has("education") ? 3
      : ["child", "children", "pediatric", "paediatric", "infant", "infants"].some((w) => words.has(w)) ? 2
        : ["adult", "adults"].some((w) => words.has(w)) ? 1 : 0;
    const hits = lists[audience] || lists[0] || "";
    return [...new Set(hits.split(",").map((id) => id.trim()).filter(Boolean))];
  }

  suggest(query: string, validIds: Map<string, number>, limit = 12): UptodateSearchSuggestion[] {
    const prefix = normalizeSearch(query);
    if (prefix.length < 2) return [];
    const current = this.aliases.get(prefix)?.[0];
    const candidates = new Map<string, { word: string; weight: number }>();
    let low = 0, high = this.vocab.length;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (this.vocab[mid] < prefix) low = mid + 1;
      else high = mid;
    }
    for (let at = low; at < this.vocab.length && this.vocab[at].startsWith(prefix); at++) {
      const word = this.vocab[at];
      const [cid, weight] = this.aliases.get(word)!;
      if (cid === current || !this.hits(cid, word).some((id) => validIds.has(id))) continue;
      const previous = candidates.get(cid);
      if (!previous || weight > previous.weight || (weight === previous.weight && (
        word.length < previous.word.length || (word.length === previous.word.length && word < previous.word)
      ))) candidates.set(cid, { word, weight });
    }
    return [...candidates.values()]
      .sort((a, b) => b.weight - a.weight || a.word.length - b.word.length || (a.word < b.word ? -1 : a.word > b.word ? 1 : 0))
      .slice(0, limit).map(({ word }) => ({
        query: word, label: word, kind: suggestionKind(word),
        count: this.hits(this.aliases.get(word)![0], word).filter((id) => validIds.has(id)).length,
      }));
  }
}
