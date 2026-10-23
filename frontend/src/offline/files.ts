import { Directory, File, Paths } from "expo-file-system";
import type { FileHandle } from "expo-file-system";

import { OfflineDataset } from "@/api/types";

/** Package parts on Android/iOS, under <documents>/offline/<dataset>/<build>/.
 * The web build's counterpart (the browser's private file system) is
 * files.web.ts. Records are read in place by offset, never whole files. */

const handles = new Map<string, FileHandle>();

function buildDir(dataset: OfflineDataset, build: string) {
  return new Directory(Paths.document, "offline", dataset, build);
}

function partFile(dataset: OfflineDataset, build: string, name: string) {
  return new File(buildDir(dataset, build), name);
}

export function ensureBuildDir(dataset: OfflineDataset, build: string) {
  buildDir(dataset, build).create({ intermediates: true, idempotent: true });
}

/** A plain filesystem path, which is what the background downloader takes. */
export function partPath(dataset: OfflineDataset, build: string, name: string): string {
  return decodeURIComponent(partFile(dataset, build, name).uri.replace(/^file:\/\//, ""));
}

export async function partSize(dataset: OfflineDataset, build: string, name: string): Promise<number> {
  const file = partFile(dataset, build, name);
  return file.exists ? file.size : 0;
}

/** True when the part on disk is exactly the published one. */
export async function verifyPart(
  dataset: OfflineDataset,
  build: string,
  part: { name: string; size: number; md5: string },
): Promise<boolean> {
  const file = partFile(dataset, build, part.name);
  return file.exists && file.size === part.size && file.md5 === part.md5;
}

export async function readRange(
  dataset: OfflineDataset,
  build: string,
  name: string,
  offset: number,
  length: number,
): Promise<Uint8Array> {
  const id = `${dataset}/${build}/${name}`;
  let handle = handles.get(id);
  if (!handle) {
    handle = partFile(dataset, build, name).open();
    handles.set(id, handle);
  }
  handle.offset = offset;
  return handle.readBytes(length);
}

function closeHandles(prefix: string) {
  for (const [id, handle] of handles) {
    if (id.startsWith(prefix)) {
      handle.close();
      handles.delete(id);
    }
  }
}

export async function removePart(dataset: OfflineDataset, build: string, name: string) {
  closeHandles(`${dataset}/${build}/${name}`);
  const file = partFile(dataset, build, name);
  if (file.exists) file.delete();
}

export async function removeBuild(dataset: OfflineDataset, build: string) {
  closeHandles(`${dataset}/${build}/`);
  const dir = buildDir(dataset, build);
  if (dir.exists) dir.delete();
}

/** Every build folder of a dataset except `keep` -- leftovers of old
 * versions or abandoned downloads. */
export async function removeOtherBuilds(dataset: OfflineDataset, keep: string[]) {
  const root = new Directory(Paths.document, "offline", dataset);
  if (!root.exists) return;
  for (const entry of root.list()) {
    if (entry instanceof Directory && !keep.includes(entry.name)) await removeBuild(dataset, entry.name);
  }
}

export async function freeBytes(): Promise<number> {
  return Paths.availableDiskSpace;
}

/** Native storage is the app's own; nothing to ask for. */
export async function requestPersistence(): Promise<boolean> {
  return true;
}
