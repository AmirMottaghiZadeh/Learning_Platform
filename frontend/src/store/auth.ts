import { create } from "zustand";

import { authApi, guestApi } from "@/api/endpoints";
import { configureAuth } from "@/api/client";
import { AuthTokenResponse, User } from "@/api/types";
import { queryClient, queryPersister } from "@/api/queryClient";
import { useNav } from "@/store/nav";
import { sessionStore } from "./session";

type Status = "loading" | "signedOut" | "signedIn";

type AuthState = {
  status: Status;
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  sessionId: string | null;
  /** Signed in with an SMS code for a forgotten password: the app asks for
   * a new password before anything else. (A brand-new account needs one
   * anyway -- `user.has_password` is false until it's chosen.) */
  mustSetPassword: boolean;
  hydrate: () => Promise<void>;
  applyAuth: (payload: AuthTokenResponse, options?: { mustSetPassword?: boolean }) => Promise<void>;
  passwordChosen: (user: User) => void;
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
  mustSetPassword: false,

  hydrate: async () => {
    const stored = await sessionStore.load();
    if (!stored) {
      // Guest access on: open the app on a throwaway account instead of the
      // sign-in screen. Any failure just means the sign-in screen.
      try {
        if ((await guestApi.status()).enabled) {
          await get().applyAuth(await guestApi.start());
          return;
        }
      } catch {
        /* fall through to signed out */
      }
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

  applyAuth: async (payload, options) => {
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
      mustSetPassword: !!options?.mustSetPassword,
      status: "signedIn",
    });
  },

  passwordChosen: (user) => set({ user, mustSetPassword: false }),

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
    // Re-entrancy guard: if the access token is already invalid, the
    // logout() call below gets its own 401, which the response
    // interceptor turns into another onAuthFailed() -> signOut() call
    // while this one is still running. Without this early check, that
    // recurses forever (each pass makes a real network call, so it never
    // shows up as a hot loop, just a hydrate() that never resolves).
    // Flipping status first makes every re-entrant call a no-op.
    if (get().status === "signedOut") return;
    set({ status: "signedOut" });
    try {
      if (get().accessToken) await authApi.logout();
    } catch {
      /* best effort */
    }
    await sessionStore.clear();
    // The query cache is also persisted to device storage -- drop both, so
    // nothing of this account shows for whoever signs in next.
    queryClient.clear();
    await queryPersister.removeClient();
    // Start the next session at Home with no history to go back through.
    useNav.getState().reset("dashboard");
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      sessionId: null,
      mustSetPassword: false,
    });
  },
}));

// Bridge the store to the axios interceptor.
configureAuth({
  getAccessToken: () => useAuth.getState().accessToken,
  refreshAccessToken: () => useAuth.getState().refresh(),
  onAuthFailed: () => useAuth.getState().signOut(),
});
