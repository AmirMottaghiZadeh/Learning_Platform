import {
  completeHandler,
  createDownloadTask,
  DownloadTask,
  getExistingDownloadTasks,
  setConfig,
} from "@kesha-antonov/react-native-background-downloader";

import { OfflineDataset } from "@/api/types";

import { partPath } from "./files";

/** Part downloads on Android/iOS, through the OS: DownloadManager / a
 * user-initiated data-transfer job (Android), a background URLSession (iOS).
 * They keep going with the app in the background or closed, and are
 * re-attached by id when it starts again. The web build's counterpart is
 * downloader.web.ts. */

export type PartRef = { dataset: OfflineDataset; build: string; name: string };
export type PartJob = PartRef & { url: string; size: number };
export type DownloadEvents = {
  progress: (part: PartRef, bytes: number) => void;
  done: (part: PartRef) => void;
  /** `status` is the HTTP status where there was one (403 = link expired) */
  error: (part: PartRef, message: string, status: number) => void;
};

/** Native transfers carry on while the app is closed. */
export const SUPPORTS_BACKGROUND = true;

const tasks = new Map<string, DownloadTask>();
let events: DownloadEvents | null = null;

const taskId = (p: PartRef) => `offline|${p.dataset}|${p.build}|${p.name}`;

function partOf(id: string): PartRef | null {
  const [tag, dataset, build, name] = id.split("|");
  if (tag !== "offline" || !build || !name || (dataset !== "uptodate" && dataset !== "lexicomp")) return null;
  return { dataset, build, name };
}

function wire(task: DownloadTask, part: PartRef) {
  task
    .progress(({ bytesDownloaded }) => events?.progress(part, bytesDownloaded))
    .done(() => {
      tasks.delete(task.id);
      completeHandler(task.id);
      events?.done(part);
    })
    .error(({ error, errorCode }) => {
      tasks.delete(task.id);
      events?.error(part, error, errorCode);
    });
  tasks.set(task.id, task);
}

export const downloader = {
  configure(options: { wifiOnly: boolean; title: string }) {
    setConfig({
      allowsCellularAccess: !options.wifiOnly,
      maxParallelDownloads: 2,
      progressInterval: 1000,
      showNotificationsEnabled: true,
      notificationsGrouping: { enabled: true, mode: "summaryOnly", texts: { groupTitle: options.title } },
    });
  },

  /** Re-attach to transfers still running (or paused) from an earlier run. */
  async attach(handlers: DownloadEvents): Promise<PartRef[]> {
    events = handlers;
    const found: PartRef[] = [];
    for (const task of await getExistingDownloadTasks()) {
      const part = partOf(task.id);
      if (!part) continue;
      wire(task, part);
      found.push(part);
    }
    return found;
  },

  isRunning(part: PartRef): boolean {
    return tasks.has(taskId(part));
  },

  start(jobs: PartJob[], title: string) {
    for (const job of jobs) {
      if (tasks.has(taskId(job))) continue;
      const task = createDownloadTask({
        id: taskId(job),
        url: job.url,
        destination: partPath(job.dataset, job.build, job.name),
        metadata: { notificationTitle: title },
      });
      wire(task, job);
      task.start();
    }
  },

  async pause(dataset: OfflineDataset) {
    for (const [id, task] of tasks) if (partOf(id)?.dataset === dataset) await task.pause();
  },

  /** Resume paused transfers; false when there were none to resume. */
  async resume(dataset: OfflineDataset): Promise<boolean> {
    let any = false;
    for (const [id, task] of tasks) {
      if (partOf(id)?.dataset === dataset && task.state === "PAUSED") {
        await task.resume();
        any = true;
      }
    }
    return any;
  },

  async stop(dataset: OfflineDataset) {
    for (const [id, task] of [...tasks]) {
      if (partOf(id)?.dataset !== dataset) continue;
      tasks.delete(id);
      await task.stop();
    }
  },
};
