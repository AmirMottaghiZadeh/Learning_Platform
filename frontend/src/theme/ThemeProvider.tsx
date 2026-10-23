import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { THEME, ThemeColors, ThemeMode, shadow } from "./tokens";

const STORAGE_KEY = "pharmexa.theme";

type ThemeContextValue = {
  mode: ThemeMode;
  colors: ThemeColors;
  shadows: ReturnType<typeof shadow>;
  isDark: boolean;
  ready: boolean;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [override, setOverride] = useState<ThemeMode | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((value) => {
        if (value === "light" || value === "dark") setOverride(value);
      })
      .finally(() => setReady(true));
  }, []);

  // Light unless the learner picked dark in the app: the phone's own dark
  // mode no longer switches it.
  const mode: ThemeMode = override ?? "light";

  const value = useMemo<ThemeContextValue>(() => {
    const setMode = (next: ThemeMode) => {
      setOverride(next);
      AsyncStorage.setItem(STORAGE_KEY, next).catch(() => undefined);
    };
    return {
      mode,
      colors: THEME[mode],
      shadows: shadow(mode),
      isDark: mode === "dark",
      ready,
      setMode,
      toggle: () => setMode(mode === "dark" ? "light" : "dark"),
    };
  }, [mode, ready]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
