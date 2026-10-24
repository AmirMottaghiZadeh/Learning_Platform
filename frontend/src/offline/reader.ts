import { strFromU8, unzlibSync } from "fflate";

import { OfflineDataset, OfflineManifest } from "@/api/types";

import { PackageKey, keyring, openRecord, openRecordBase64 } from "./crypto";
import { readRange } from "./files";

/** [part, offset, length] of one sealed record. */
export type Locator = [number, number, number];

const CHECK = "pharmenta-offline";

/** Opens records of one installed build: reads the bytes by offset,
 * decrypts, and inflates JSON/text records. */
export class PackageReader {
  constructor(
    readonly dataset: OfflineDataset,
    readonly manifest: OfflineManifest,
    private readonly key: PackageKey,
  ) {}

  private async sealed([part, offset, length]: Locator): Promise<Uint8Array> {
    const file = this.manifest.files[part];
    if (!file) throw new Error(`no part ${part}`);
    return readRange(this.dataset, this.manifest.build, file.name, offset, length);
  }

  async bytes(loc: Locator): Promise<Uint8Array> {
    return openRecord(this.key, await this.sealed(loc));
  }

  async base64(loc: Locator): Promise<string> {
    return openRecordBase64(this.key, await this.sealed(loc));
  }

  async text(loc: Locator): Promise<string> {
    return strFromU8(unzlibSync(await this.bytes(loc)));
  }

  async json<T>(loc: Locator): Promise<T> {
    return JSON.parse(await this.text(loc)) as T;
  }

  index<T>(): Promise<T> {
    return this.json<T>(this.manifest.index);
  }

  /** Throws unless the key opens this build's check record. */
  async verify(): Promise<void> {
    const sealed = new Uint8Array(this.manifest.check.length / 2);
    for (let i = 0; i < sealed.length; i++) sealed[i] = parseInt(this.manifest.check.slice(i * 2, i * 2 + 2), 16);
    if (strFromU8(await openRecord(this.key, sealed)) !== CHECK) throw new Error("wrong package key");
  }
}

const open = new Map<string, Promise<PackageReader>>();

/** A verified reader for an installed build, shared until closed. */
export function openReader(dataset: OfflineDataset, manifest: OfflineManifest): Promise<PackageReader> {
  const id = `${dataset}:${manifest.build}`;
  let reader = open.get(id);
  if (!reader) {
    reader = (async () => {
      const key = await keyring.load(dataset, manifest.build);
      if (!key) throw new Error("no package key");
      const created = new PackageReader(dataset, manifest, key);
      await created.verify();
      return created;
    })();
    open.set(id, reader);
    reader.catch(() => open.delete(id));
  }
  return reader;
}

export function closeReaders(dataset: OfflineDataset) {
  for (const id of [...open.keys()]) if (id.startsWith(`${dataset}:`)) open.delete(id);
}
