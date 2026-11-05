import { SearchPageArgs, lexicompApi, uptodateApi } from "@/api/endpoints";
import { ApiError } from "@/api/client";
import { queryClient } from "@/api/queryClient";
import { LexicompDrug, LexicompInteraction, OfflineDataset, UptodateArticle, UptodateImage, UptodateSearchPage, UptodateSearchResult } from "@/api/types";

import { checkInteractions, searchDrugs } from "./lexicompLocal";
import { PackageReader, openReader } from "./reader";
import { isUsable, renewLicense, touch, useOffline } from "./store";
import { forgetUptodate, getImage, getTopic, searchTopics, searchTopicsPage } from "./uptodateLocal";
import { refreshSearchSupplement } from "./uptodateSearchSupplement";

/** Where the UpToDate and Lexicomp screens get their data: the package on
 * this device first, when one is installed and its license is good; the
 * online API otherwise -- and also whenever reading the package fails, so a
 * damaged or half-removed package never leaves a screen empty. */

async function localReader(dataset: OfflineDataset): Promise<PackageReader | null> {
  // Renewal is cheap when it isn't due; done in passing, never awaited.
  void renewLicense(dataset);
  if (!isUsable(dataset)) return null;
  const manifest = useOffline.getState().datasets[dataset].installed?.manifest;
  if (!manifest) return null;
  try {
    const reader = await openReader(dataset, manifest);
    touch(dataset);
    if (dataset === "uptodate") {
      void refreshSearchSupplement(reader).then((updated) => {
        if (updated) {
          forgetUptodate();
          void queryClient.invalidateQueries({ queryKey: ["uptodate-search-page"] });
        }
      }).catch(() => undefined);
    }
    return reader;
  } catch {
    // e.g. the key went missing: a forced renewal puts it back.
    void renewLicense(dataset, { force: true });
    return null;
  }
}

async function localFirst<T>(
  dataset: OfflineDataset,
  local: (reader: PackageReader) => Promise<T | null>,
  online: () => Promise<T>,
): Promise<T> {
  const reader = await localReader(dataset);
  if (reader) {
    try {
      const answer = await local(reader);
      if (answer !== null) return answer;
    } catch {
      /* fall through to the API */
    }
  }
  return online();
}

export const uptodateSource = {
  search: (search: string, limit = 25): Promise<UptodateSearchResult[]> =>
    localFirst("uptodate", (r) => searchTopics(r, search, limit), () => uptodateApi.search(search, limit)),
  searchPage: (search: string, args: SearchPageArgs = {}): Promise<UptodateSearchPage> =>
    localFirst("uptodate", (r) => searchTopicsPage(r, search, args), () => uptodateApi.searchPage(search, args)),
  topic: (id: string): Promise<UptodateArticle> =>
    localFirst("uptodate", (r) => getTopic(r, id), () => uptodateApi.topic(id)),
  topicAtAnchor: async (id: string, contentHash: string, anchor: string): Promise<UptodateArticle> => {
    try {
      return await uptodateApi.topicAtAnchor(id, contentHash, anchor);
    } catch (error) {
      if (error instanceof ApiError && error.status !== 503) throw error;
      // The downloaded article may be an older revision. Without the server's
      // hash check, omit anchor status so the reader starts at the top.
      return uptodateSource.topic(id);
    }
  },
  image: (id: string): Promise<UptodateImage> =>
    localFirst("uptodate", (r) => getImage(r, id), () => uptodateApi.image(id)),
};

export const lexicompSource = {
  search: (search: string, limit = 20): Promise<LexicompDrug[]> =>
    localFirst("lexicomp", (r) => searchDrugs(r, search, limit), () => lexicompApi.search(search, limit)),
  checkInteractions: (genericIds: number[]): Promise<LexicompInteraction[]> =>
    localFirst("lexicomp", (r) => checkInteractions(r, genericIds), () => lexicompApi.checkInteractions(genericIds)),
};
