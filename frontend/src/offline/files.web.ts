import { OfflineDataset } from "@/api/types";

/** Package parts in the browser's origin-private file system (OPFS), under
 * offline/<dataset>/<build>/. Written by the download worker
 * (downloader.web.ts); read here by byte range without loading a part. */

const snapshots = new Map<string, File>();

async function dir(path: string[], create: boolean): Promise<FileSystemDirectoryHandle | null> {
  let handle = await navigator.storage.getDirectory();
  for (const name of ["offline", ...path]) {
    try {
      handle = await handle.getDirectoryHandle(name, { create });
    } catch {
      return null;
    }
  }
  return handle;
}

async function file(dataset: OfflineDataset, build: string, name: string): Promise<File | null> {
  const parent = await dir([dataset, build], false);
  if (!parent) return null;
  try {
    return await (await parent.getFileHandle(name)).getFile();
  } catch {
    return null;
  }
}

export async function ensureBuildDir(dataset: OfflineDataset, build: string) {
  await dir([dataset, build], true);
}

export function partPath(dataset: OfflineDataset, build: string, name: string): string {
  return `offline/${dataset}/${build}/${name}`;
}

export async function partSize(dataset: OfflineDataset, build: string, name: string): Promise<number> {
  return (await file(dataset, build, name))?.size ?? 0;
}

/** Size only: every record is authenticated on its own when opened, and
 * hashing 100 MB in the page would be slow and memory-hungry. */
export async function verifyPart(
  dataset: OfflineDataset,
  build: string,
  part: { name: string; size: number; md5: string },
): Promise<boolean> {
  return (await partSize(dataset, build, part.name)) === part.size;
}

export async function readRange(
  dataset: OfflineDataset,
  build: string,
  name: string,
  offset: number,
  length: number,
): Promise<Uint8Array> {
  const id = `${dataset}/${build}/${name}`;
  let snapshot = snapshots.get(id);
  if (!snapshot) {
    const found = await file(dataset, build, name);
    if (!found) throw new Error(`missing part ${id}`);
    snapshot = found;
    snapshots.set(id, snapshot);
  }
  return new Uint8Array(await snapshot.slice(offset, offset + length).arrayBuffer());
}

function forget(prefix: string) {
  for (const id of [...snapshots.keys()]) if (id.startsWith(prefix)) snapshots.delete(id);
}

export async function removePart(dataset: OfflineDataset, build: string, name: string) {
  forget(`${dataset}/${build}/${name}`);
  const parent = await dir([dataset, build], false);
  await parent?.removeEntry(name).catch(() => undefined);
}

export async function removeBuild(dataset: OfflineDataset, build: string) {
  forget(`${dataset}/${build}/`);
  const parent = await dir([dataset], false);
  await parent?.removeEntry(build, { recursive: true }).catch(() => undefined);
}

export async function removeOtherBuilds(dataset: OfflineDataset, keep: string[]) {
  const parent = await dir([dataset], false);
  if (!parent) return;
  const names: string[] = [];
  for await (const [name, handle] of parent.entries()) if (handle.kind === "directory") names.push(name);
  for (const name of names) if (!keep.includes(name)) await removeBuild(dataset, name);
}

export async function freeBytes(): Promise<number> {
  const { quota = 0, usage = 0 } = await navigator.storage.estimate();
  return Math.max(0, quota - usage);
}

/** Ask the browser not to evict the packages under storage pressure. */
export async function requestPersistence(): Promise<boolean> {
  try {
    return (await navigator.storage.persisted()) || (await navigator.storage.persist());
  } catch {
    return false;
  }
}
