import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { ApiError } from "@/api/client";
import { offlineApi } from "@/api/endpoints";
import { OfflineDataset, OfflineManifest, OfflinePackageInfo } from "@/api/types";
import { useAuth } from "@/store/auth";

import { keyring } from "./crypto";
import { DownloadEvents, PartRef, SUPPORTS_BACKGROUND, downloader } from "./downloader";
import * as files from "./files";
import { closeReaders, openReader } from "./reader";

/** The offline packages on this device: what is installed, what is being
 * downloaded, and the license that lets the app open each one.
 *
 * Lifecycle of a dataset: download() publishes a `pending` build whose
 * parts are fetched (by the OS on Android/iOS, by a worker on the web);
 * once every part is on disk and checks out, a license (the key) is fetched
 * and the build becomes `installed`, replacing any older one. The license
 * is renewed whenever the app is online; `isUsable()` decides whether the
 * readers may open the installed build right now. */

export const DATASETS: OfflineDataset[] = ["uptodate", "lexicomp"];

/** Renew a license this long after the last renewal, when online -- so a
 * plan that ended locks the package within this while the app is in use
 * (and at once on the next start, which always renews). */
const RENEW_AFTER_MS = 30 * 60 * 1000;
/** Clock drift tolerated before a backwards-set clock locks the package. */
const CLOCK_SLACK_MS = 10 * 60 * 1000;
/** Room left free on the device beyond the package itself. */
const SPACE_MARGIN_BYTES = 64 * 1024 * 1024;
/** Re-download of parts that arrive damaged, per build, before giving up. */
const MAX_REPAIRS = 2;

export type OfflineErrorCode =
  | "not_entitled"
  | "not_published"
  | "no_space"
  | "network"
  | "damaged"
  | "failed";

export class OfflineError extends Error {
  constructor(readonly code: OfflineErrorCode) {
    super(code);
    this.name = "OfflineError";
  }
}

export type OfflineLicenseState = {
  userId: number;
  /** how long the server let it run, measured from `renewedAt` */
  validForMs: number;
  /** device time of the last renewal */
  renewedAt: number;
  /** latest device time seen while it was in use: a clock set back past
   * this locks the package until the next renewal */
  lastSeenAt: number;
};

export type InstalledPackage = {
  manifest: OfflineManifest;
  installedAt: number;
  license: OfflineLicenseState | null;
  /** the server refused to renew: the plan ended or does not include it */
  locked: boolean;
};

export type PendingStatus = "downloading" | "paused" | "verifying" | "error";

export type PendingPackage = {
  manifest: OfflineManifest;
  status: PendingStatus;
  /** bytes on disk per part */
  received: Record<string, number>;
  urls: Record<string, string>;
  urlsExpireAt: number;
  error: OfflineErrorCode | null;
  repairs: number;
};

export type DatasetState = { installed: InstalledPackage | null; pending: PendingPackage | null };

type OfflineState = {
  datasets: Record<OfflineDataset, DatasetState>;
  /** the last answer of GET /offline/packages/ */
  remote: Partial<Record<OfflineDataset, OfflinePackageInfo>>;
  wifiOnly: boolean;
  hydrated: boolean;
};

const empty = (): Record<OfflineDataset, DatasetState> => ({
  uptodate: { installed: null, pending: null },
  lexicomp: { installed: null, pending: null },
});

export const useOffline = create<OfflineState>()(
  persist(
    (): OfflineState => ({ datasets: empty(), remote: {}, wifiOnly: true, hydrated: false }),
    {
      name: "pharmenta.offline",
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ datasets: s.datasets, remote: s.remote, wifiOnly: s.wifiOnly }),
      onRehydrateStorage: () => () => useOffline.setState({ hydrated: true }),
    },
  ),
);

const get = () => useOffline.getState();

function patch(dataset: OfflineDataset, change: Partial<DatasetState>) {
  useOffline.setState((s) => ({ datasets: { ...s.datasets, [dataset]: { ...s.datasets[dataset], ...change } } }));
}

function patchPending(dataset: OfflineDataset, change: Partial<PendingPackage>) {
  const pending = get().datasets[dataset].pending;
  if (pending) patch(dataset, { pending: { ...pending, ...change } });
}

function patchInstalled(dataset: OfflineDataset, change: Partial<InstalledPackage>) {
  const installed = get().datasets[dataset].installed;
  if (installed) patch(dataset, { installed: { ...installed, ...change } });
}

const currentUserId = () => useAuth.getState().user?.id ?? null;
const notificationTitle = () => "دانلود دیتابیس آفلاین فارمنتا";

// --- reading --------------------------------------------------------------

/** Whether the readers may open `dataset`'s installed build right now. */
export function isUsable(dataset: OfflineDataset, now = Date.now()): boolean {
  const installed = get().datasets[dataset].installed;
  const license = installed?.license;
  if (!installed || installed.locked || !license) return false;
  if (license.userId !== currentUserId()) return false;
  if (now < license.renewedAt - CLOCK_SLACK_MS || now < license.lastSeenAt - CLOCK_SLACK_MS) return false;
  return now - license.renewedAt <= license.validForMs;
}

/** Note the device time a package was used at (for the clock check). */
export function touch(dataset: OfflineDataset, now = Date.now()) {
  const license = get().datasets[dataset].installed?.license;
  if (license && now - license.lastSeenAt > 60_000) {
    patchInstalled(dataset, { license: { ...license, lastSeenAt: Math.max(license.lastSeenAt, now) } });
  }
}

export function licenseExpiresAt(dataset: OfflineDataset): number | null {
  const license = get().datasets[dataset].installed?.license;
  return license ? license.renewedAt + license.validForMs : null;
}

// --- server ---------------------------------------------------------------

function isNetworkError(error: unknown) {
  return !(error instanceof ApiError);
}

export async function refreshRemote(): Promise<Partial<Record<OfflineDataset, OfflinePackageInfo>>> {
  const rows = await offlineApi.packages();
  const remote: Partial<Record<OfflineDataset, OfflinePackageInfo>> = {};
  for (const row of rows) remote[row.dataset] = row;
  useOffline.setState({ remote });
  return remote;
}

/** Fetch (or refresh) the license of the installed build. Refused -> the
 * package locks and its key is dropped; no network -> nothing changes. */
const renewing = new Map<OfflineDataset, Promise<void>>();

export function renewLicense(dataset: OfflineDataset, options: { force?: boolean } = {}): Promise<void> {
  let running = renewing.get(dataset);
  if (!running) {
    running = renewOnce(dataset, !!options.force).finally(() => renewing.delete(dataset));
    renewing.set(dataset, running);
  }
  return running;
}

async function renewOnce(dataset: OfflineDataset, force: boolean): Promise<void> {
  const installed = get().datasets[dataset].installed;
  const userId = currentUserId();
  if (!installed || userId == null) return;
  const license = installed.license;
  const fresh =
    license && license.userId === userId && !installed.locked && Date.now() - license.renewedAt < RENEW_AFTER_MS;
  if (fresh && !force) return;
  const build = installed.manifest.build;
  try {
    const answer = await offlineApi.license(dataset, build, await keyring.publicKey());
    await keyring.save(dataset, answer);
    const now = Date.now();
    patchInstalled(dataset, {
      locked: false,
      license: {
        userId,
        validForMs: Math.max(0, Date.parse(answer.valid_until) - Date.parse(answer.server_time)),
        renewedAt: now,
        lastSeenAt: now,
      },
    });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 402 || error.status === 404)) {
      closeReaders(dataset);
      await keyring.remove(dataset, build).catch(() => undefined);
      patchInstalled(dataset, { locked: true, license: null });
    }
  }
}

// --- downloading ----------------------------------------------------------

const progressFlush = new Map<OfflineDataset, ReturnType<typeof setTimeout>>();
const liveReceived: Record<OfflineDataset, Record<string, number>> = { uptodate: {}, lexicomp: {} };

function samePending(part: PartRef) {
  const pending = get().datasets[part.dataset].pending;
  return pending && pending.manifest.build === part.build ? pending : null;
}

const events: DownloadEvents = {
  progress(part, bytes) {
    if (!samePending(part)) return;
    liveReceived[part.dataset][part.name] = bytes;
    // Progress comes in many times a second: write it to the store at most
    // twice a second.
    if (progressFlush.has(part.dataset)) return;
    progressFlush.set(
      part.dataset,
      setTimeout(() => {
        progressFlush.delete(part.dataset);
        const pending = get().datasets[part.dataset].pending;
        if (pending) patchPending(part.dataset, { received: { ...pending.received, ...liveReceived[part.dataset] } });
      }, 500),
    );
  },
  done(part) {
    const pending = samePending(part);
    if (!pending) return;
    const size = pending.manifest.files.find((f) => f.name === part.name)?.size ?? 0;
    liveReceived[part.dataset][part.name] = size;
    patchPending(part.dataset, { received: { ...pending.received, [part.name]: size } });
    const after = get().datasets[part.dataset].pending;
    if (after && after.manifest.files.every((f) => (after.received[f.name] ?? 0) >= f.size)) {
      void finish(part.dataset);
    }
  },
  error(part, _message, status) {
    const pending = samePending(part);
    if (!pending || pending.status === "paused") return;
    // An expired or refused link: fetch fresh ones and carry on.
    if ([400, 401, 403].includes(status)) {
      void refreshUrlsAndStart(part.dataset).catch(() => patchPending(part.dataset, { status: "error", error: "network" }));
      return;
    }
    void downloader.stop(part.dataset);
    patchPending(part.dataset, { status: "error", error: status ? "failed" : "network" });
  },
};

async function refreshUrlsAndStart(dataset: OfflineDataset) {
  const pending = get().datasets[dataset].pending;
  if (!pending) return;
  const answer = await offlineApi.urls(dataset, pending.manifest.build);
  patchPending(dataset, {
    urls: Object.fromEntries(answer.files.map((f) => [f.name, f.url])),
    urlsExpireAt: Date.parse(answer.expires_at),
  });
  await startParts(dataset);
}

/** Start every part not yet on disk (and not already being fetched). */
async function startParts(dataset: OfflineDataset) {
  const pending = get().datasets[dataset].pending;
  if (!pending) return;
  // Links within the last hour of their life: get new ones first.
  if (pending.urlsExpireAt - Date.now() < 60 * 60 * 1000) return refreshUrlsAndStart(dataset);
  const { manifest } = pending;
  await files.ensureBuildDir(dataset, manifest.build);
  const received = { ...pending.received };
  const jobs = [];
  for (const file of manifest.files) {
    const part = { dataset, build: manifest.build, name: file.name };
    if (downloader.isRunning(part)) continue;
    let have = await files.partSize(dataset, manifest.build, file.name);
    if (have >= file.size) {
      received[file.name] = file.size;
      continue;
    }
    // The OS downloaders start a part over; only the web worker continues
    // a partial file.
    if (have > 0 && SUPPORTS_BACKGROUND) {
      await files.removePart(dataset, manifest.build, file.name);
      have = 0;
    }
    received[file.name] = have;
    jobs.push({ ...part, url: pending.urls[file.name], size: file.size });
  }
  liveReceived[dataset] = { ...received };
  patchPending(dataset, { status: "downloading", error: null, received });
  if (jobs.length) downloader.start(jobs, notificationTitle());
  else await finish(dataset);
}

/** Download the latest published build of `dataset` (or carry on with it). */
export async function download(dataset: OfflineDataset): Promise<void> {
  let info: OfflinePackageInfo | undefined;
  try {
    info = (await refreshRemote())[dataset];
  } catch (error) {
    throw new OfflineError(isNetworkError(error) ? "network" : "failed");
  }
  if (!info?.entitled) throw new OfflineError("not_entitled");
  const manifest = info.package;
  if (!manifest) throw new OfflineError("not_published");

  const state = get().datasets[dataset];
  if (state.installed?.manifest.build === manifest.build) {
    // Already here; a locked one only needs its license back.
    if (state.installed.locked) await renewLicense(dataset, { force: true });
    return;
  }
  if (state.pending && state.pending.manifest.build !== manifest.build) await cancel(dataset);

  await files.requestPersistence();
  await files.ensureBuildDir(dataset, manifest.build);
  let have = 0;
  for (const f of manifest.files) have += Math.min(await files.partSize(dataset, manifest.build, f.name), f.size);
  if ((await files.freeBytes()) < manifest.total_size - have + SPACE_MARGIN_BYTES) {
    throw new OfflineError("no_space");
  }

  let urls;
  try {
    urls = await offlineApi.urls(dataset, manifest.build);
  } catch (error) {
    if (error instanceof ApiError && error.status === 402) throw new OfflineError("not_entitled");
    throw new OfflineError(isNetworkError(error) ? "network" : "failed");
  }
  patch(dataset, {
    pending: {
      manifest,
      status: "downloading",
      received: get().datasets[dataset].pending?.received ?? {},
      urls: Object.fromEntries(urls.files.map((f) => [f.name, f.url])),
      urlsExpireAt: Date.parse(urls.expires_at),
      error: null,
      repairs: get().datasets[dataset].pending?.repairs ?? 0,
    },
  });
  downloader.configure({ wifiOnly: get().wifiOnly, title: notificationTitle() });
  await startParts(dataset);
}

export async function pause(dataset: OfflineDataset) {
  if (!get().datasets[dataset].pending) return;
  patchPending(dataset, { status: "paused" });
  await downloader.pause(dataset);
}

export async function resume(dataset: OfflineDataset) {
  const pending = get().datasets[dataset].pending;
  if (!pending) return;
  if (pending.status === "verifying") return;
  patchPending(dataset, { status: "downloading", error: null });
  try {
    downloader.configure({ wifiOnly: get().wifiOnly, title: notificationTitle() });
    await downloader.resume(dataset);
    await startParts(dataset);
  } catch (error) {
    patchPending(dataset, { status: "error", error: isNetworkError(error) ? "network" : "failed" });
  }
}

/** Abandon the download in progress and delete what it fetched. */
export async function cancel(dataset: OfflineDataset) {
  const pending = get().datasets[dataset].pending;
  await downloader.stop(dataset);
  patch(dataset, { pending: null });
  liveReceived[dataset] = {};
  if (pending && pending.manifest.build !== get().datasets[dataset].installed?.manifest.build) {
    await files.removeBuild(dataset, pending.manifest.build);
  }
}

/** Delete the installed package (and any download) from this device. */
export async function remove(dataset: OfflineDataset) {
  await cancel(dataset);
  const installed = get().datasets[dataset].installed;
  closeReaders(dataset);
  patch(dataset, { installed: null });
  if (installed) {
    await keyring.remove(dataset, installed.manifest.build).catch(() => undefined);
    await files.removeBuild(dataset, installed.manifest.build);
  }
  await files.removeOtherBuilds(dataset, []);
}

export function setWifiOnly(wifiOnly: boolean) {
  useOffline.setState({ wifiOnly });
  downloader.configure({ wifiOnly, title: notificationTitle() });
}

/** Every part is on disk: check it, get its key, and switch over to it. */
async function finish(dataset: OfflineDataset) {
  const pending = get().datasets[dataset].pending;
  if (!pending || pending.status === "verifying") return;
  const { manifest } = pending;
  patchPending(dataset, { status: "verifying", error: null });

  const damaged = [];
  for (const file of manifest.files) {
    if (!(await files.verifyPart(dataset, manifest.build, file))) damaged.push(file.name);
  }
  if (damaged.length) {
    for (const name of damaged) await files.removePart(dataset, manifest.build, name);
    const received = { ...pending.received };
    for (const name of damaged) received[name] = 0;
    if (pending.repairs >= MAX_REPAIRS) {
      patchPending(dataset, { status: "error", error: "damaged", received });
      return;
    }
    patchPending(dataset, { status: "downloading", received, repairs: pending.repairs + 1 });
    await startParts(dataset);
    return;
  }

  const userId = currentUserId();
  let license;
  try {
    if (userId == null) throw new OfflineError("network");
    license = await offlineApi.license(dataset, manifest.build, await keyring.publicKey());
    await keyring.save(dataset, license);
    const reader = await openReader(dataset, manifest);
    await reader.index();
  } catch (error) {
    const code: OfflineErrorCode =
      error instanceof ApiError && error.status === 402
        ? "not_entitled"
        : error instanceof OfflineError || isNetworkError(error)
          ? "network"
          : "damaged";
    closeReaders(dataset);
    patchPending(dataset, { status: "error", error: code });
    return;
  }

  const previous = get().datasets[dataset].installed;
  const now = Date.now();
  patch(dataset, {
    pending: null,
    installed: {
      manifest,
      installedAt: now,
      locked: false,
      license: {
        userId,
        validForMs: Math.max(0, Date.parse(license.valid_until) - Date.parse(license.server_time)),
        renewedAt: now,
        lastSeenAt: now,
      },
    },
  });
  liveReceived[dataset] = {};
  if (previous && previous.manifest.build !== manifest.build) {
    closeReaders(dataset);
    await keyring.remove(dataset, previous.manifest.build).catch(() => undefined);
  }
  // keep the new build only; the old one is no longer referenced
  void openReader(dataset, manifest).catch(() => undefined);
  await files.removeOtherBuilds(dataset, [manifest.build]);
}

// --- start-up -------------------------------------------------------------

let booted: Promise<void> | null = null;

/** Once per app start, after sign-in: re-attach to transfers that went on
 * while the app was closed, carry on downloads that were running, and
 * renew licenses and the published-builds list when online. */
export function bootOffline(): Promise<void> {
  booted ??= (async () => {
    if (!get().hydrated) {
      await new Promise<void>((resolve) => {
        const stop = useOffline.subscribe((s) => {
          if (s.hydrated) {
            stop();
            resolve();
          }
        });
      });
    }
    downloader.configure({ wifiOnly: get().wifiOnly, title: notificationTitle() });
    await downloader.attach(events).catch(() => []);
    for (const dataset of DATASETS) {
      const pending = get().datasets[dataset].pending;
      if (pending?.status === "downloading" || pending?.status === "verifying") {
        if (pending.status === "verifying") patchPending(dataset, { status: "downloading" });
        await startParts(dataset).catch(() => patchPending(dataset, { status: "error", error: "network" }));
      }
    }
    await Promise.all(DATASETS.map((dataset) => renewLicense(dataset, { force: true })));
    await refreshRemote().catch(() => undefined);
  })();
  return booted;
}

/** Signing out (or another account signing in) re-checks on the next boot. */
export function resetOfflineBoot() {
  booted = null;
}

/** Bytes of the pending build on disk, live. */
export function pendingBytes(pending: PendingPackage): number {
  return pending.manifest.files.reduce((sum, f) => sum + Math.min(pending.received[f.name] ?? 0, f.size), 0);
}
