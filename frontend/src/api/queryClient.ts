import AsyncStorage from "@react-native-async-storage/async-storage";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import { QueryClient } from "@tanstack/react-query";
import type { PersistedClient, Persister } from "@tanstack/react-query-persist-client";

import { ApiError } from "./client";

const MINUTE = 60_000;
const DAY = 24 * 60 * MINUTE;

/** How long a cached answer survives an app restart. Also the in-memory
 * gcTime: React Query only persists queries it still holds, so gcTime must be
 * at least this long or entries would be dropped before they're restored. */
export const CACHE_MAX_AGE = 7 * DAY;
/** Bump whenever an API response shape changes: a cache written by an older
 * build is then discarded on start instead of being fed to newer code. */
export const CACHE_BUSTER = "2026-10-17";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError && [401, 403, 404, 422].includes(error.status)) {
          return false;
        }
        return failureCount < 2;
      },
      // Restored data shows immediately; anything older than this is
      // refetched quietly in the background when its screen mounts.
      staleTime: 5 * MINUTE,
      gcTime: CACHE_MAX_AGE,
      refetchOnWindowFocus: false,
    },
  },
});

// Reference content that only changes when the dataset is re-imported --
// no reason to refetch it within a day. An EMPTY answer is the exception:
// it means the data wasn't there yet (e.g. asked before the import), so it
// is never trusted as fresh -- otherwise a list fetched before the import
// would keep showing as empty for a day after it.
const isEmptyList = (data: unknown) => Array.isArray(data) && data.length === 0;
const REFERENCE_KEYS = ["calculators", "calculator-categories", "calculator", "medscape-tree", "lesson-drug"];
for (const key of REFERENCE_KEYS) {
  queryClient.setQueryDefaults([key], { staleTime: (query) => (isEmptyList(query.state.data) ? 0 : DAY) });
}

// UpToDate and Lexicomp read the package on this device first (see
// src/offline/sources.ts), so they must run with no network as well: React
// Query would otherwise park them as "paused" until it sees a connection.
for (const key of ["uptodate-search", "uptodate-topic", "uptodate-graphic-html", "lexicomp-search"]) {
  queryClient.setQueryDefaults([key], { networkMode: "always" });
}

// --- persistence across app restarts ---------------------------------------
//
// Only small, reused answers are written to device storage. Android's
// AsyncStorage can't read back a single value much over 2 MB (and the web's
// localStorage caps at ~5 MB overall), so whole Medscape/UpToDate articles,
// images and one-off searches stay in memory only, per-item caches keep just
// their most recent entries, and the total is trimmed oldest-first.
const PERSISTED_KEYS = new Set([
  "dashboard",
  "statistics",
  "plan",
  "plan-today",
  "mistakes",
  "lesson-groups",
  "chapter",
  "lesson-drug",
  "flashcards-due",
  "flashcards-boxes",
  "quiz-overview",
  "calculators",
  "calculator-categories",
  "calculator",
  "medscape-tree",
  "medscape-articles",
  "medscape-recent",
]);
/** Per-item caches (one entry per drug / calculator opened): keep the newest. */
const MOST_RECENT = { "lesson-drug": 20, calculator: 20 } as Record<string, number>;
/** Serialized size budget, in characters, comfortably under the 2 MB limit. */
const MAX_PERSISTED_CHARS = 1_200_000;

type DehydratedQuery = PersistedClient["clientState"]["queries"][number];

function trimForStorage(client: PersistedClient): PersistedClient {
  let queries = client.clientState.queries.filter(
    (q) =>
      q.state.status === "success" &&
      PERSISTED_KEYS.has(String(q.queryKey[0])) &&
      // never carry an empty reference list over a restart (see REFERENCE_KEYS)
      !(REFERENCE_KEYS.includes(String(q.queryKey[0])) && isEmptyList(q.state.data)),
  );

  const newestFirst = (a: DehydratedQuery, b: DehydratedQuery) => b.state.dataUpdatedAt - a.state.dataUpdatedAt;
  const dropped = new Set<string>();
  for (const [key, keep] of Object.entries(MOST_RECENT)) {
    queries
      .filter((q) => q.queryKey[0] === key)
      .sort(newestFirst)
      .slice(keep)
      .forEach((q) => dropped.add(q.queryHash));
  }
  queries = queries.filter((q) => !dropped.has(q.queryHash));

  // Still over budget: drop the oldest answers until it fits.
  const sizeOf = (q: DehydratedQuery) => JSON.stringify(q).length;
  let total = queries.reduce((sum, q) => sum + sizeOf(q), 0);
  if (total > MAX_PERSISTED_CHARS) {
    const byAge = [...queries].sort(newestFirst);
    while (total > MAX_PERSISTED_CHARS && byAge.length) {
      const oldest = byAge.pop()!;
      total -= sizeOf(oldest);
      dropped.add(oldest.queryHash);
    }
    queries = queries.filter((q) => !dropped.has(q.queryHash));
  }

  return { ...client, clientState: { ...client.clientState, queries, mutations: [] } };
}

const storagePersister = createAsyncStoragePersister({
  storage: AsyncStorage,
  key: "pharmenta.query-cache",
  throttleTime: 2000,
});

export const queryPersister: Persister = {
  persistClient: (client) => storagePersister.persistClient(trimForStorage(client)),
  restoreClient: () => storagePersister.restoreClient(),
  removeClient: () => storagePersister.removeClient(),
};
