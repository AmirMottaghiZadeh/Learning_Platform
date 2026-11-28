import { OfflineDataset } from "@/api/types";

/** Part downloads in the browser / PWA. A small worker fetches each part and
 * writes it straight into the origin-private file system with a sync access
 * handle (the one OPFS writer every current browser has), continuing a part
 * from the bytes already on disk with a Range request. Runs only while the
 * page is open; the store restarts it on the next visit. */

export type PartRef = { dataset: OfflineDataset; build: string; name: string };
export type PartJob = PartRef & { url: string; size: number };
export type DownloadEvents = {
  progress: (part: PartRef, bytes: number) => void;
  done: (part: PartRef) => void;
  error: (part: PartRef, message: string, status: number) => void;
};

export const SUPPORTS_BACKGROUND = false;

const WORKER_SOURCE = `
let controller = null;
self.onmessage = async (event) => {
  const msg = event.data;
  if (msg.type === "abort") { if (controller) controller.abort(); return; }
  if (msg.type !== "start") return;
  controller = new AbortController();
  let handle = null;
  try {
    let dir = await navigator.storage.getDirectory();
    for (const name of msg.path.slice(0, -1)) dir = await dir.getDirectoryHandle(name, { create: true });
    const file = await dir.getFileHandle(msg.path[msg.path.length - 1], { create: true });
    handle = await file.createSyncAccessHandle();
    let at = handle.getSize();
    if (at > msg.size) { handle.truncate(0); at = 0; }
    if (at < msg.size) {
      const res = await fetch(msg.url, { headers: at ? { Range: "bytes=" + at + "-" } : {}, signal: controller.signal });
      if (res.status === 200 && at) { handle.truncate(0); at = 0; }
      else if (!res.ok) { const e = new Error("HTTP " + res.status); e.status = res.status; throw e; }
      const reader = res.body.getReader();
      let last = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        handle.write(value, { at });
        at += value.byteLength;
        const now = Date.now();
        if (now - last > 500) { last = now; self.postMessage({ type: "progress", bytes: at }); }
      }
    }
    handle.flush();
    handle.close();
    handle = null;
    self.postMessage(at === msg.size ? { type: "done" } : { type: "error", message: "size " + at + " of " + msg.size, status: 0 });
  } catch (err) {
    try { if (handle) { handle.flush(); handle.close(); } } catch (_) {}
    if (err && err.name === "AbortError") self.postMessage({ type: "aborted" });
    else self.postMessage({ type: "error", message: String((err && err.message) || err), status: (err && err.status) || 0 });
  }
};
`;

type Run = { worker: Worker; queue: PartJob[]; current: PartJob | null };

const runs = new Map<OfflineDataset, Run>();
let events: DownloadEvents | null = null;
let workerUrl: string | null = null;

function newWorker(): Worker {
  workerUrl ??= URL.createObjectURL(new Blob([WORKER_SOURCE], { type: "text/javascript" }));
  return new Worker(workerUrl);
}

function next(run: Run) {
  const job = run.queue.shift() ?? null;
  run.current = job;
  if (!job) return;
  run.worker.postMessage({
    type: "start",
    path: ["offline", job.dataset, job.build, job.name],
    url: job.url,
    size: job.size,
  });
}

function runFor(dataset: OfflineDataset): Run {
  let run = runs.get(dataset);
  if (run) return run;
  const worker = newWorker();
  const created: Run = { worker, queue: [], current: null };
  worker.onmessage = (event: MessageEvent) => {
    const job = created.current;
    if (!job) return;
    const msg = event.data as { type: string; bytes?: number; message?: string; status?: number };
    if (msg.type === "progress") events?.progress(job, msg.bytes ?? 0);
    else if (msg.type === "done") {
      events?.progress(job, job.size);
      events?.done(job);
      next(created);
    } else if (msg.type === "error") {
      created.current = null;
      created.queue = [];
      events?.error(job, msg.message ?? "failed", msg.status ?? 0);
    }
  };
  runs.set(dataset, created);
  return created;
}

export const downloader = {
  configure(_options: { wifiOnly: boolean; title: string }) {
    // A page can't tell Wi-Fi from mobile data reliably; nothing to set.
  },

  async attach(handlers: DownloadEvents): Promise<PartRef[]> {
    events = handlers;
    return [];
  },

  isRunning(part: PartRef): boolean {
    const run = runs.get(part.dataset);
    return !!run && [run.current, ...run.queue].some((j) => j?.build === part.build && j.name === part.name);
  },

  start(jobs: PartJob[], _title: string) {
    for (const job of jobs) {
      if (downloader.isRunning(job)) continue;
      runFor(job.dataset).queue.push(job);
    }
    for (const run of runs.values()) if (!run.current) next(run);
  },

  /** Ends the worker outright: the bytes already written stay, and a fresh
   * worker continues from them (a lingering one would still hold the
   * part's access handle). */
  async pause(dataset: OfflineDataset) {
    await downloader.stop(dataset);
  },

  /** Nothing is held paused here: the store starts the remaining parts again. */
  async resume(_dataset: OfflineDataset): Promise<boolean> {
    return false;
  },

  async stop(dataset: OfflineDataset) {
    const run = runs.get(dataset);
    if (!run) return;
    run.worker.terminate();
    runs.delete(dataset);
  },
};
