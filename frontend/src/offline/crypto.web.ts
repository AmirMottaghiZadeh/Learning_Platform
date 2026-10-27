import { OfflineDataset, OfflineLicense } from "@/api/types";

/** Package keys in the browser / PWA. The browser makes an RSA-OAEP key
 * pair whose private half can't be exported, sends the public half with
 * the license request, and gets the package key back wrapped to it; the
 * unwrapped AES key is non-extractable too. Both live in IndexedDB as
 * CryptoKey objects: page script can decrypt with them but never read
 * their bytes, and the raw key never appears in a response. */

export type PackageKey = CryptoKey;

const NONCE_BYTES = 12;
const DB_NAME = "pharmenta-offline";
const STORE = "keys";
const RSA_ID = "rsa";

function db(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idb<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest): Promise<T> {
  const conn = await db();
  try {
    return await new Promise<T>((resolve, reject) => {
      const req = run(conn.transaction(STORE, mode).objectStore(STORE));
      req.onsuccess = () => resolve(req.result as T);
      req.onerror = () => reject(req.error);
    });
  } finally {
    conn.close();
  }
}

const keyId = (dataset: OfflineDataset, build: string) => `${dataset}:${build}`;

async function rsaPair(): Promise<CryptoKeyPair> {
  const existing = await idb<CryptoKeyPair | undefined>("readonly", (s) => s.get(RSA_ID));
  if (existing) return existing;
  const pair = await crypto.subtle.generateKey(
    { name: "RSA-OAEP", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    false,
    ["unwrapKey"],
  );
  await idb("readwrite", (s) => s.put(pair, RSA_ID));
  return pair;
}

function toBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

function fromBase64(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}

export const keyring = {
  async publicKey(): Promise<string | undefined> {
    const spki = await crypto.subtle.exportKey("spki", (await rsaPair()).publicKey);
    return toBase64(new Uint8Array(spki));
  },
  async save(dataset: OfflineDataset, license: OfflineLicense): Promise<void> {
    if (!license.wrapped_key) throw new Error("license without a wrapped key");
    const key = await crypto.subtle.unwrapKey(
      "raw",
      fromBase64(license.wrapped_key),
      (await rsaPair()).privateKey,
      { name: "RSA-OAEP" },
      { name: "AES-GCM" },
      false,
      ["decrypt"],
    );
    await idb("readwrite", (s) => s.put(key, keyId(dataset, license.build)));
  },
  async load(dataset: OfflineDataset, build: string): Promise<PackageKey | null> {
    return (await idb<CryptoKey | undefined>("readonly", (s) => s.get(keyId(dataset, build)))) ?? null;
  },
  async remove(dataset: OfflineDataset, build: string): Promise<void> {
    await idb("readwrite", (s) => s.delete(keyId(dataset, build)));
  },
};

export async function openRecord(key: PackageKey, record: Uint8Array): Promise<Uint8Array> {
  // Records are read into plain ArrayBuffers (never shared memory).
  const bytes = record as Uint8Array<ArrayBuffer>;
  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: bytes.subarray(0, NONCE_BYTES) },
    key,
    bytes.subarray(NONCE_BYTES),
  );
  return new Uint8Array(plain);
}

export async function openRecordBase64(key: PackageKey, record: Uint8Array): Promise<string> {
  return toBase64(await openRecord(key, record));
}
