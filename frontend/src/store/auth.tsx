import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {createContext, useCallback, useContext, useEffect, useMemo, useState} from "react";

import {platformApi} from "../api/platform";
import type {RegisterPayload, User} from "../types/api";

type AuthState = {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
  signIn: (username: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  signOut: () => Promise<void>;
};

const TOKEN_KEY = "pharmexa_auth_token";
const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({children}: {children: React.ReactNode}) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadSession() {
      try {
        const storedToken = await AsyncStorage.getItem(TOKEN_KEY);
        if (!storedToken) return;
        const profile = await platformApi.me(storedToken);
        if (!active) return;
        setToken(storedToken);
        setUser(profile);
      } catch {
        await AsyncStorage.removeItem(TOKEN_KEY);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadSession();
    return () => {
      active = false;
    };
  }, []);

  const applyAuth = useCallback(async (nextToken: string, nextUser: User) => {
    await AsyncStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
    setUser(nextUser);
    setError(null);
  }, []);

  const signIn = useCallback(
    async (username: string, password: string) => {
      setLoading(true);
      try {
        const response = await platformApi.login(username, password);
        await applyAuth(response.token, response.user);
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "ورود با خطا مواجه شد.");
        throw exc;
      } finally {
        setLoading(false);
      }
    },
    [applyAuth],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      setLoading(true);
      try {
        const response = await platformApi.register(payload);
        await applyAuth(response.token, response.user);
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "ثبت‌نام با خطا مواجه شد.");
        throw exc;
      } finally {
        setLoading(false);
      }
    },
    [applyAuth],
  );

  const signOut = useCallback(async () => {
    const currentToken = token;
    setToken(null);
    setUser(null);
    await AsyncStorage.removeItem(TOKEN_KEY);
    if (currentToken) {
      try {
        await platformApi.logout(currentToken);
      } catch {
        // Local sign-out must succeed even if the backend token was already invalidated.
      }
    }
  }, [token]);

  const value = useMemo(
    () => ({token, user, loading, error, signIn, register, signOut}),
    [token, user, loading, error, signIn, register, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
