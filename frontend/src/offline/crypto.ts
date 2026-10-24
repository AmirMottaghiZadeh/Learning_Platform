import { AESEncryptionKey, AESSealedData, aesDecryptAsync } from "expo-crypto";
import * as SecureStore from "expo-secure-store";

import { OfflineDataset, OfflineLicense } from "@/api/types";

/** Package keys on Android/iOS: the license hands over the raw key, which is
 * kept in the Keystore/Keychain (expo-secure-store) and never anywhere else.
 * The web build's counterpart is crypto.web.ts. */

export type PackageKey = AESEncryptionKey;

const NONCE_BYTES = 12;
const TAG_BYTES = 16;
const storeName = (dataset: OfflineDataset, build: string) => `pharmenta.offline.${dataset}.${build}`;

export const keyring = {
  /** What the license request sends to have the key wrapped; native sends none. */
  async publicKey(): Promise<string | undefined> {
    return undefined;
  },
  async save(dataset: OfflineDataset, license: OfflineLicense): Promise<void> {
    if (!license.key) throw new Error("license without a key");
    await SecureStore.setItemAsync(storeName(dataset, license.build), license.key);
  },
  async load(dataset: OfflineDataset, build: string): Promise<PackageKey | null> {
    const value = await SecureStore.getItemAsync(storeName(dataset, build));
    return value ? AESEncryptionKey.import(value, "base64") : null;
  },
  async remove(dataset: OfflineDataset, build: string): Promise<void> {
    await SecureStore.deleteItemAsync(storeName(dataset, build));
  },
};

function sealed(record: Uint8Array) {
  return AESSealedData.fromCombined(record, { ivLength: NONCE_BYTES, tagLength: TAG_BYTES });
}

/** nonce || ciphertext || tag -> plaintext; throws on a wrong key or damage. */
export async function openRecord(key: PackageKey, record: Uint8Array): Promise<Uint8Array> {
  return aesDecryptAsync(sealed(record), key);
}

/** The same, as base64 (images go straight into a data: URI). */
export async function openRecordBase64(key: PackageKey, record: Uint8Array): Promise<string> {
  return aesDecryptAsync(sealed(record), key, { output: "base64" });
}
