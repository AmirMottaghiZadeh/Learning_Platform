import type { LexicompDrug, LexicompInteraction } from "@/api/types";

import type { Locator, PackageReader } from "./reader";

/** Lexicomp answered from the installed package, in the API's own shapes.
 * A port of apps/lexicomp/services.py: the drug search's LIKE-and-rank, and
 * `check_interactions` with the same role/exception rules and row order. */

type LexIndex = {
  generics: [number, string][];
  brands: [number, number, string][];
  xref: [number, number][];
  severity: Record<string, string>;
  reliability: Record<string, string>;
  /** [id, object_id, precipitant_id, severity_id, reliability_id, part, offset, length] */
  monographs: number[][];
  exceptions: [number, number, number][];
};

type Prepared = {
  index: LexIndex;
  names: Map<number, string>;
  drugs: (LexicompDrug & { lower: string })[];
  categoriesOf: Map<number, Set<number>>;
  /** monograph rows by precipitant category, in id order */
  byPrecipitant: Map<number, number[][]>;
  exceptionsOf: Map<number, [number, number][]>;
};

const cache = new Map<string, Promise<Prepared>>();

function prepared(reader: PackageReader): Promise<Prepared> {
  const build = reader.manifest.build;
  let entry = cache.get(build);
  if (!entry) {
    entry = reader.index<LexIndex>().then((index) => {
      const categoriesOf = new Map<number, Set<number>>();
      for (const [category, generic] of index.xref) {
        let set = categoriesOf.get(generic);
        if (!set) categoriesOf.set(generic, (set = new Set()));
        set.add(category);
      }
      const byPrecipitant = new Map<number, number[][]>();
      for (const row of [...index.monographs].sort((a, b) => a[0] - b[0])) {
        const list = byPrecipitant.get(row[2]);
        if (list) list.push(row);
        else byPrecipitant.set(row[2], [row]);
      }
      const exceptionsOf = new Map<number, [number, number][]>();
      for (const [monograph, category, generic] of index.exceptions) {
        const list = exceptionsOf.get(monograph);
        if (list) list.push([category, generic]);
        else exceptionsOf.set(monograph, [[category, generic]]);
      }
      // The order SQLite scans them in, which breaks the search's ties:
      // generics by name (its covering index), brands by id.
      const byName = [...index.generics].sort(([, a], [, b]) => (a < b ? -1 : a > b ? 1 : 0));
      const drugs = [
        ...byName.map(([id, name]) => ({ id, name, generic_id: id, kind: "generic" as const })),
        ...index.brands.map(([id, generic_id, name]) => ({ id, name, generic_id, kind: "brand" as const })),
      ].map((d) => ({ ...d, lower: d.name.toLowerCase() }));
      return { index, names: new Map(index.generics), drugs, categoriesOf, byPrecipitant, exceptionsOf };
    });
    cache.clear();
    cache.set(build, entry);
    entry.catch(() => cache.delete(build));
  }
  return entry;
}

/** Generic and brand names containing the query, those starting with it
 * first, then shortest first -- `search_drugs`. */
export async function searchDrugs(reader: PackageReader, query: string, limit = 20): Promise<LexicompDrug[]> {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const { drugs } = await prepared(reader);
  return drugs
    .filter((d) => d.lower.includes(q))
    .map((d, order) => ({ d, order, rank: d.lower.startsWith(q) ? 0 : 1 }))
    .sort((a, b) => a.rank - b.rank || a.d.name.length - b.d.name.length || a.order - b.order)
    .slice(0, limit)
    .map(({ d }) => ({ id: d.id, name: d.name, generic_id: d.generic_id, kind: d.kind }));
}

const SEVERITY_RANK: Record<string, number> = { major: 0, moderate: 1, minor: 2 };

type Texts = { summary: string; management: string; discussion: string; footnotes: string };

export async function checkInteractions(reader: PackageReader, genericIds: number[]): Promise<LexicompInteraction[]> {
  const ids = [...new Set(genericIds.map(Number))].sort((a, b) => a - b);
  if (ids.length < 2) return [];
  const { index, names, categoriesOf, byPrecipitant, exceptionsOf } = await prepared(reader);
  const none = new Set<number>();

  // (monograph, a, b) in the order the server's query yields them.
  const matches = new Map<string, { row: number[]; a: number; b: number }>();
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const a = ids[i];
      const b = ids[j];
      const catsA = categoriesOf.get(a) ?? none;
      const catsB = categoriesOf.get(b) ?? none;
      if (!catsA.size || !catsB.size) continue;
      const seen = new Set<number>();
      const scan = (precipitants: Set<number>, objects: Set<number>) => {
        for (const p of [...precipitants].sort((x, y) => x - y)) {
          for (const row of byPrecipitant.get(p) ?? []) {
            if (objects.has(row[1]) && !seen.has(row[0])) {
              seen.add(row[0]);
              matches.set(`${row[0]}|${a}|${b}`, { row, a, b });
            }
          }
        }
      };
      scan(catsB, catsA);
      scan(catsA, catsB);
    }
  }

  const results: (LexicompInteraction & { rank: number })[] = [];
  for (const { row, a, b } of matches.values()) {
    const [monographId, objectId, precipitantId, severityId, reliabilityId] = row;
    const catsA = categoriesOf.get(a) ?? none;
    const catsB = categoriesOf.get(b) ?? none;
    const candidates: [number, number][] = [];
    if (catsA.has(objectId) && catsB.has(precipitantId)) candidates.push([a, b]);
    if (catsB.has(objectId) && catsA.has(precipitantId)) candidates.push([b, a]);
    const excepted = exceptionsOf.get(monographId) ?? [];
    const exceptedObject = new Set(excepted.filter(([c]) => c === objectId).map(([, g]) => g));
    const exceptedPrecipitant = new Set(excepted.filter(([c]) => c === precipitantId).map(([, g]) => g));
    const valid = candidates.filter(([obj, prec]) => !exceptedObject.has(obj) && !exceptedPrecipitant.has(prec));
    if (!valid.length) continue;
    const [objectDrug, precipitantDrug] = valid[0];
    const texts = await reader.json<Texts>(row.slice(5, 8) as Locator);
    const severity = index.severity[String(severityId)] ?? "N/A";
    results.push({
      monograph_id: monographId,
      drug_ids: [a, b],
      object_generic_id: objectDrug,
      object_name: names.get(objectDrug) ?? "",
      precipitant_generic_id: precipitantDrug,
      precipitant_name: names.get(precipitantDrug) ?? "",
      severity,
      reliability: index.reliability[String(reliabilityId)] ?? "",
      summary: texts.summary,
      management: texts.management,
      discussion: texts.discussion,
      footnotes: texts.footnotes,
      rank: SEVERITY_RANK[severity.toLowerCase()] ?? 99,
    });
  }
  return results.sort((x, y) => x.rank - y.rank).map(({ rank: _rank, ...r }) => r);
}

export function forgetLexicomp() {
  cache.clear();
}
