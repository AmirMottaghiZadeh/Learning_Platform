import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { View, ViewStyle, StyleProp } from "react-native";

import type { TourKey } from "./tours";

/**
 * The guided tours: one per section of the app, played the first time the
 * learner opens that section (home's right after onboarding), skippable, and
 * replayed by the section's "?" button. A step rings one real element -- a
 * TourTarget -- and shows a small animated preview of what it does with a
 * line or two of text (TourOverlay; the steps are in tours.ts).
 *
 * Which tours were seen is kept on the device.
 */

export type Rect = { x: number; y: number; w: number; h: number };

type Target = {
  /** Where the element is, in window coordinates; null when not on screen. */
  measure: () => Promise<Rect | null>;
  /** Scroll the element's screen until it is in view (TourScroll). */
  reveal?: (rect: Rect) => Promise<void>;
};

type TourContextValue = {
  /** Which tour is playing, if any. */
  active: TourKey | null;
  /** Seen tours are loaded from the device. */
  loaded: boolean;
  isSeen: (key: TourKey) => boolean;
  start: (key: TourKey) => void;
  /** End the playing tour; it counts as seen. */
  finish: () => void;
  register: (id: string, target: Target) => () => void;
  target: (id: string) => Target | undefined;
};

const SEEN_KEY = "pharmexa.toursSeen.v1";

const TourContext = createContext<TourContextValue | null>(null);

export function TourProvider({ children }: { children: React.ReactNode }) {
  const targets = useRef(new Map<string, Target>()).current;
  const seenRef = useRef<Set<TourKey>>(new Set());
  const activeRef = useRef<TourKey | null>(null);
  const [seen, setSeen] = useState<Set<TourKey>>(new Set());
  const [loaded, setLoaded] = useState(false);
  const [active, setActive] = useState<TourKey | null>(null);

  useEffect(() => {
    AsyncStorage.getItem(SEEN_KEY)
      .then((raw) => {
        seenRef.current = new Set(JSON.parse(raw ?? "[]"));
        setSeen(seenRef.current);
      })
      .catch(() => undefined)
      .finally(() => setLoaded(true));
  }, []);

  const start = useCallback((key: TourKey) => {
    activeRef.current = key;
    setActive(key);
  }, []);

  const finish = useCallback(() => {
    const key = activeRef.current;
    activeRef.current = null;
    setActive(null);
    if (!key || seenRef.current.has(key)) return;
    seenRef.current = new Set(seenRef.current).add(key);
    setSeen(seenRef.current);
    AsyncStorage.setItem(SEEN_KEY, JSON.stringify([...seenRef.current])).catch(() => undefined);
  }, []);

  const register = useCallback(
    (id: string, target: Target) => {
      targets.set(id, target);
      return () => {
        if (targets.get(id) === target) targets.delete(id);
      };
    },
    [targets],
  );
  const target = useCallback((id: string) => targets.get(id), [targets]);

  const value = useMemo<TourContextValue>(
    () => ({ active, loaded, isSeen: (key) => seen.has(key), start, finish, register, target }),
    [active, loaded, seen, start, finish, register, target],
  );

  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}

export function useTourContext() {
  return useContext(TourContext);
}

/** Plays `key`'s tour once `ready` (the screen's content is on screen), the
 * first time only. Returns a function that replays it -- the "?" button. */
export function useTour(key: TourKey, ready = true) {
  const tour = useContext(TourContext);
  const shouldStart = !!tour && tour.loaded && ready && !tour.isSeen(key) && !tour.active;
  useEffect(() => {
    if (!shouldStart) return;
    // let the screen's entrance animation and layout settle first
    const timer = setTimeout(() => tour?.start(key), 900);
    return () => clearTimeout(timer);
  }, [shouldStart, key, tour]);
  return useCallback(() => tour?.start(key), [tour, key]);
}

/** How a scrolling screen brings an element into view for the tour. */
export type TourScroller = { reveal: (rect: Rect) => Promise<void> };
export const TourScrollContext = createContext<TourScroller | null>(null);

/** Marks one element a tour step can point at, by `id` (tours.ts). */
export function TourTarget({
  id,
  children,
  style,
}: {
  id: string;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const ref = useRef<View>(null);
  const tour = useContext(TourContext);
  const scroller = useContext(TourScrollContext);
  useEffect(() => {
    if (!tour) return;
    return tour.register(id, {
      measure: () =>
        new Promise((resolve) => {
          const node = ref.current;
          if (!node) return resolve(null);
          node.measureInWindow((x, y, w, h) => resolve(w || h ? { x, y, w, h } : null));
        }),
      reveal: scroller ? (rect) => scroller.reveal(rect) : undefined,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- register is stable
  }, [id, scroller, tour?.register]);
  return (
    <View ref={ref} collapsable={false} style={style}>
      {children}
    </View>
  );
}
