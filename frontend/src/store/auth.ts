import { create } from "zustand";

import { authApi } from "@/api/endpoints";
import { configureAuth } from "@/api/client";
import { AuthTokenResponse, User } from "@/api/types";
import { queryClient } from "@/api/queryClient";
import { sessionStore } from "./session";

type Status = "loading" | "signedOut" | "signedIn";

type AuthState = {
  status: Status;
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  sessionId: string | null;
  hydrate: () => Promise<void>;
  applyAuth: (payload: AuthTokenResponse) => Promise<void>;
  setUser: (user: User) => void;
  refresh: () => Promise<string>;
  signOut: () => Promise<void>;
};

export const useAuth = create<AuthState>((set, get) => ({
  status: "loading",
  user: null,
  accessToken: null,
  refreshToken: null,
  sessionId: null,

  hydrate: async () => {
    const stored = await sessionStore.load();
    if (!stored) {
      set({ status: "signedOut" });
      return;
    }
    set({
      accessToken: stored.accessToken || null,
      refreshToken: stored.refreshToken,
      sessionId: stored.sessionId || null,
    });
    try {
      const user = stored.accessToken ? await authApi.me() : null;
      if (user) {
        set({ user, status: "signedIn" });
      } else {
        await get().refresh();
        set({ user: await authApi.me(), status: "signedIn" });
      }
    } catch {
      await get().signOut();
    }
  },

  applyAuth: async (payload) => {
    await sessionStore.save({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      sessionId: payload.session_id,
    });
    set({
      user: payload.user,
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      sessionId: payload.session_id,
      status: "signedIn",
    });
  },

  setUser: (user) => set({ user }),

  refresh: async () => {
    const token = get().refreshToken;
    if (!token) throw new Error("no refresh token");
    const payload = await authApi.refresh(token);
    await sessionStore.save({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      sessionId: payload.session_id,
    });
    set({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      sessionId: payload.session_id,
      user: payload.user,
    });
    return payload.access_token;
  },

  signOut: async () => {
    try {
      if (get().accessToken) await authApi.logout();
    } catch {
      /* best effort */
    }
    await sessionStore.clear();
    queryClient.clear();
    set({
      status: "signedOut",
      user: null,
      accessToken: null,
      refreshToken: null,
      sessionId: null,
    });
  },
}));

// Bridge the store to the axios interceptor.
configureAuth({
  getAccessToken: () => useAuth.getState().accessToken,
  refreshAccessToken: () => useAuth.getState().refresh(),
  onAuthFailed: () => useAuth.getState().signOut(),
});
