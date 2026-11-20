import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

import type { User } from "@/api/types";

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

/** The signed-in user's profile as last seen online: what the app starts
 * with when it is opened without internet. Not a credential. */
const USER_KEY = "pharmexa.user";

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
    await Promise.all([
      set(KEYS.access, null),
      set(KEYS.refresh, null),
      set(KEYS.session, null),
      AsyncStorage.removeItem(USER_KEY),
    ]);
  },
  async saveUser(user: User | null) {
    await (user ? AsyncStorage.setItem(USER_KEY, JSON.stringify(user)) : AsyncStorage.removeItem(USER_KEY));
  },
  async loadUser(): Promise<User | null> {
    try {
      const raw = await AsyncStorage.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  },
};
