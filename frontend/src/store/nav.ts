import { create } from "zustand";

import { ScreenKey, TabKey } from "@/navigation/types";

type NavState = {
  screen: ScreenKey;
  params: Record<string, unknown>;
  history: ScreenKey[];
  navigate: (screen: ScreenKey, params?: Record<string, unknown>) => void;
  /** Switch bottom-nav tab (resets the in-tab stack). */
  setTab: (tab: TabKey) => void;
  goBack: () => void;
  reset: (screen: ScreenKey) => void;
};

export const useNav = create<NavState>((set, get) => ({
  screen: "dashboard",
  params: {},
  history: [],

  navigate: (screen, params = {}) =>
    set((s) => ({ screen, params, history: [...s.history, s.screen] })),

  setTab: (tab) => set({ screen: tab, params: {}, history: [] }),

  goBack: () =>
    set((s) => {
      if (s.history.length === 0) return { screen: "dashboard", params: {}, history: [] };
      const history = s.history.slice(0, -1);
      return { screen: s.history[s.history.length - 1], params: {}, history };
    }),

  reset: (screen) => set({ screen, params: {}, history: [] }),
}));
