import { apiClient } from "@/api/client";

import { partSize, readRange, writePart } from "./files";
import type { PackageReader } from "./reader";
import type { SearchCatalogData } from "./uptodateSearchCatalog";

export type SearchSupplement = {
  schema: number;
  version: string;
  memberships: Record<string, string[]>;
  search: SearchCatalogData;
};

const FILE = "search-v1.bin";
const loaded = new Map<string, Promise<SearchSupplement | null>>();
const attempted = new Map<string, number>();

function validate(data: SearchSupplement, version: string): SearchSupplement {
  if (data.schema !== 1 || data.version !== version || !Array.isArray(data.search?.queries)
      || !data.search.topics || !data.memberships) throw new Error("incompatible search supplement");
  return data;
}

export function loadSearchSupplement(reader: PackageReader, version: string): Promise<SearchSupplement | null> {
  const build = reader.manifest.build;
  let promise = loaded.get(build);
  if (!promise) {
    promise = (async () => {
      try {
        const size = await partSize("uptodate", build, FILE);
        if (!size) return null;
        return validate(await reader.decodeJson<SearchSupplement>(await readRange("uptodate", build, FILE, 0, size)), version);
      } catch { return null; }
    })();
    loaded.set(build, promise);
  }
  return promise;
}

/** Runs in the background. A failed request leaves local search usable. */
export async function refreshSearchSupplement(reader: PackageReader): Promise<boolean> {
  const index = await reader.index<{ version: string; search_schema?: number }>();
  if (index.search_schema === 1 || await loadSearchSupplement(reader, index.version)) return false;
  const build = reader.manifest.build;
  if (Date.now() - (attempted.get(build) ?? 0) < 60_000) return false;
  attempted.set(build, Date.now());
  try {
    const response = await apiClient.get<ArrayBuffer>("/uptodate/search-metadata/", {
      params: { build, version: index.version }, responseType: "arraybuffer",
    });
    const bytes = new Uint8Array(response.data);
    const data = validate(await reader.decodeJson<SearchSupplement>(bytes), index.version);
    await writePart("uptodate", build, FILE, bytes);
    loaded.set(build, Promise.resolve(data));
    return true;
  } catch { return false; }
}
