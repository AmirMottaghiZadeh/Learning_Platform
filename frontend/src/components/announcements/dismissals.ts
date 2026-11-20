import AsyncStorage from "@react-native-async-storage/async-storage";
import { announcementsApi } from "@/api/endpoints";
import { useAuth } from "@/store/auth";

type Saved = { hidden: number[]; pending: number[] };
let tail = Promise.resolve();
const memory = new Map<number, Saved>();
const syncing = new Map<number, Promise<void>>();

// Serialize read/modify/write so a retry cannot overwrite a second dismissal.
function serial<T>(work: () => Promise<T>): Promise<T> {
  const result = tail.then(work);
  tail = result.then(() => undefined, () => undefined);
  return result;
}
const key = (userId: number) => `pharmenta:announcement-dismissals:${userId}`;
async function read(userId: number): Promise<Saved> {
  if (memory.has(userId)) return memory.get(userId)!;
  try {
    const saved = JSON.parse((await AsyncStorage.getItem(key(userId))) ?? "null");
    if (saved && Array.isArray(saved.hidden) && Array.isArray(saved.pending)) {
      return { hidden: saved.hidden.filter(Number.isInteger), pending: saved.pending.filter(Number.isInteger) };
    }
  } catch { /* fall back to this session if storage is unavailable */ }
  return { hidden: [], pending: [] };
}
async function save(userId: number, value: Saved) {
  memory.set(userId, value);
  await AsyncStorage.setItem(key(userId), JSON.stringify(value)).catch(() => undefined);
}
export function loadDismissals(userId: number) {
  return serial(async () => (await read(userId)).hidden);
}
export function rememberDismissal(userId: number, id: number) {
  return serial(async () => {
    const saved = await read(userId);
    await save(userId, { hidden: [...new Set([...saved.hidden, id])], pending: [...new Set([...saved.pending, id])] });
  });
}
export function syncDismissals(userId: number) {
  if (syncing.has(userId)) return syncing.get(userId)!;
  const run = (async () => {
    const pending = await serial(async () => [...(await read(userId)).pending]);
    const sent = new Set<number>();
    for (const id of pending) {
      if (useAuth.getState().user?.id !== userId) break;
      try { await announcementsApi.event(id, "dismiss"); sent.add(id); }
      catch (error) {
        // Deleted announcements no longer need a receipt.
        if ((error as { status?: number }).status === 404) sent.add(id);
      }
    }
    // Network waits must not hold the storage lock: another dismissal should
    // be durable immediately even while a previous request is still offline.
    await serial(async () => {
      const saved = await read(userId);
      await save(userId, { hidden: saved.hidden, pending: saved.pending.filter((id) => !sent.has(id)) });
    });
  })().finally(() => { syncing.delete(userId); });
  syncing.set(userId, run);
  return run;
}
