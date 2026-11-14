import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { BG_TONES, DEFAULT_TONE, THEME, ThemeColors, ThemeMode, shadow } from "./tokens";

const STORAGE_KEY = "pharmexa.theme";
/** The background tone picked for each theme: {"light": 0..3, "dark": 0..3}. */
const TONE_KEY = "pharmenta.bgTone";

export type Tones = Record<ThemeMode, number>;
const DEFAULT_TONES: Tones = { light: DEFAULT_TONE, dark: DEFAULT_TONE };

function validTone(mode: ThemeMode, value: unknown): number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 && value < BG_TONES[mode].length
    ? value
    : DEFAULT_TONE;
}

type ThemeContextValue = {
  mode: ThemeMode;
  colors: ThemeColors;
  shadows: ReturnType<typeof shadow>;
  isDark: boolean;
  ready: boolean;
  /** the background tone picked for each theme (Settings) */
  tones: Tones;
  setMode: (mode: ThemeMode) => void;
  setTone: (mode: ThemeMode, tone: number) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [override, setOverride] = useState<ThemeMode | null>(null);
  const [tones, setTones] = useState<Tones>(DEFAULT_TONES);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([
      AsyncStorage.getItem(STORAGE_KEY).then((value) => {
        if (value === "light" || value === "dark") setOverride(value);
      }),
      AsyncStorage.getItem(TONE_KEY).then((raw) => {
        if (!raw) return;
        const saved = JSON.parse(raw) as Partial<Tones>;
        setTones({ light: validTone("light", saved.light), dark: validTone("dark", saved.dark) });
      }),
    ])
      .catch(() => undefined)
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
    const setTone = (which: ThemeMode, tone: number) => {
      const next = { ...tones, [which]: validTone(which, tone) };
      setTones(next);
      AsyncStorage.setItem(TONE_KEY, JSON.stringify(next)).catch(() => undefined);
    };
    return {
      mode,
      colors: { ...THEME[mode], ...BG_TONES[mode][tones[mode]] },
      shadows: shadow(mode),
      isDark: mode === "dark",
      ready,
      tones,
      setMode,
      setTone,
      toggle: () => setMode(mode === "dark" ? "light" : "dark"),
    };
  }, [mode, ready, tones]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
