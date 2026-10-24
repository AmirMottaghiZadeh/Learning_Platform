import { create } from "zustand";

import { ScreenKey, TabKey } from "@/navigation/types";

type HistoryEntry = { screen: ScreenKey; params: Record<string, unknown> };

/** How the current screen was reached -- drives its enter animation:
 * "forward" slides in from the trailing edge, "back" from the leading edge,
 * "tab" (bottom-nav switch or reset) just fades. */
export type NavDirection = "forward" | "back" | "tab";

type NavState = {
  screen: ScreenKey;
  params: Record<string, unknown>;
  history: HistoryEntry[];
  direction: NavDirection;
  /** Bumped on every transition, so the same screen reached twice in a row
   * (e.g. one calculator, then another) still replays its enter animation. */
  transitionId: number;
  navigate: (screen: ScreenKey, params?: Record<string, unknown>) => void;
  /** Switch bottom-nav tab (resets the in-tab stack). */
  setTab: (tab: TabKey) => void;
  goBack: () => void;
  reset: (screen: ScreenKey) => void;
};

export const useNav = create<NavState>((set) => ({
  screen: "dashboard",
  params: {},
  history: [],
  direction: "tab",
  transitionId: 0,

  navigate: (screen, params = {}) =>
    set((s) => ({
      screen,
      params,
      history: [...s.history, { screen: s.screen, params: s.params }],
      direction: "forward",
      transitionId: s.transitionId + 1,
    })),

  setTab: (tab) =>
    set((s) => ({ screen: tab, params: {}, history: [], direction: "tab", transitionId: s.transitionId + 1 })),

  goBack: () =>
    set((s) => {
      const transitionId = s.transitionId + 1;
      if (s.history.length === 0)
        return { screen: "dashboard", params: {}, history: [], direction: "back", transitionId };
      const history = s.history.slice(0, -1);
      const previous = s.history[s.history.length - 1];
      return { screen: previous.screen, params: previous.params, history, direction: "back", transitionId };
    }),

  reset: (screen) =>
    set((s) => ({ screen, params: {}, history: [], direction: "tab", transitionId: s.transitionId + 1 })),
}));
