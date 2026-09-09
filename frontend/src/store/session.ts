import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

/**
 * Token storage: expo-secure-store on native, AsyncStorage on web (SecureStore
 * is unavailable there). Only the refresh token really needs to persist; the
 * access token is kept too so a warm start skips one refresh round-trip.
 */

const KEYS = {
  access: "pharmexa.access",
  refresh: "pharmexa.refresh",
  session: "pharmexa.session",
} as const;

const web = Platform.OS === "web";

async function set(key: string, value: string | null) {
  if (value == null) {
    return web ? AsyncStorage.removeItem(key) : SecureStore.deleteItemAsync(key);
  }
  return web ? AsyncStorage.setItem(key, value) : SecureStore.setItemAsync(key, value);
}

async function get(key: string) {
  return web ? AsyncStorage.getItem(key) : SecureStore.getItemAsync(key);
}

export type StoredSession = {
  accessToken: string;
  refreshToken: string;
  sessionId: string;
};

export const sessionStore = {
  async load(): Promise<StoredSession | null> {
    const [accessToken, refreshToken, sessionId] = await Promise.all([
      get(KEYS.access),
      get(KEYS.refresh),
      get(KEYS.session),
    ]);
    if (!refreshToken) return null;
    return { accessToken: accessToken ?? "", refreshToken, sessionId: sessionId ?? "" };
  },
  async save(s: StoredSession) {
    await Promise.all([
      set(KEYS.access, s.accessToken),
      set(KEYS.refresh, s.refreshToken),
      set(KEYS.session, s.sessionId),
    ]);
  },
  async clear() {
    await Promise.all([set(KEYS.access, null), set(KEYS.refresh, null), set(KEYS.session, null)]);
  },
};
