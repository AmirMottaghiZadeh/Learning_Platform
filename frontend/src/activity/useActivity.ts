import { useEffect } from "react";
import { AppState, Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Crypto from "expo-crypto";
import { apiClient } from "@/api/client";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";

type Event = { id: string; section: string; action: "view" | "engagement" | "click"; duration_seconds: number; x?: number; y?: number; area?: "screen" | "article"; viewport?: "mobile" | "tablet" | "desktop" };
const writers = new Map<string, Promise<void>>();
const flushing = new Set<string>();
let clickCapture: ((x: number, y: number, area: "screen" | "article", width: number) => void) | null = null;

export function recordClick(x: number, y: number, area: "screen" | "article" = "screen", width = 430) {
  if (Number.isFinite(x) && Number.isFinite(y)) clickCapture?.(x, y, area, width);
}

/** Only section identifiers and visible time are recorded, never article IDs,
 * queries, message contents or form inputs. Queues are isolated by account. */
export function useActivity() {
  const screen = useNav(s => s.screen);
  const userId = useAuth(s => s.status === "signedIn" ? s.user?.id : null);
  useEffect(() => {
    if (!userId || screen === "auth") return;
    const key = `pharmenta.activity.${userId}`;
    let active = AppState.currentState === "active" || Platform.OS === "web";
    let documentVisible = Platform.OS !== "web" || typeof document === "undefined" || !document.hidden;
    let started = Date.now(), stopped = false;
    const visible = () => active && documentVisible;
    const enqueue = (event: Event) => {
      const operation = (writers.get(key) || Promise.resolve()).then(async () => {
        try {
          const events: Event[] = JSON.parse(await AsyncStorage.getItem(key) || "[]");
          events.push(event);
          await AsyncStorage.setItem(key, JSON.stringify(events.slice(-500)));
        } catch { /* Analytics storage must never block reading. */ }
      });
      writers.set(key, operation);
    };
    const capture = (x: number, y: number, area: "screen" | "article", width: number) => {
      if (visible()) enqueue({ id: Crypto.randomUUID(), section: screen, action: "click", duration_seconds: 0, x: Math.round(Math.max(0, Math.min(100, x))), y: Math.round(Math.max(0, Math.min(100, y))), area, viewport: width <= 600 ? "mobile" : width <= 1100 ? "tablet" : "desktop" });
    };
    clickCapture = capture;
    const flush = async () => {
      if (flushing.has(key) || stopped || useAuth.getState().user?.id !== userId || useAuth.getState().status !== "signedIn") return;
      flushing.add(key);
      await writers.get(key);
      try {
        const events: Event[] = JSON.parse(await AsyncStorage.getItem(key) || "[]");
        const batch = events.slice(0, 100);
        if (!batch.length) return;
        await apiClient.post("/activity/events/", { events: batch });
        const ids = new Set(batch.map(e => e.id));
        const operation = (writers.get(key) || Promise.resolve()).then(async () => {
          const current: Event[] = JSON.parse(await AsyncStorage.getItem(key) || "[]");
          await AsyncStorage.setItem(key, JSON.stringify(current.filter(e => !ids.has(e.id))));
        });
        writers.set(key, operation);
        await operation;
      } catch { /* Retry on the next visible heartbeat. */ }
      finally { flushing.delete(key); }
    };
    const heartbeat = () => {
      const elapsed = Math.min(120, Math.floor((Date.now() - started) / 1000));
      if (visible() && elapsed > 0) enqueue({ id: Crypto.randomUUID(), section: screen, action: "engagement", duration_seconds: elapsed });
      started = Date.now();
    };
    enqueue({ id: Crypto.randomUUID(), section: screen, action: "view", duration_seconds: 0 });
    void flush();
    const sub = AppState.addEventListener("change", state => { heartbeat(); active = state === "active"; started = Date.now(); if (active) void flush(); });
    const visibility = () => { heartbeat(); documentVisible = !document.hidden; if (visible()) void flush(); };
    if (Platform.OS === "web") document.addEventListener("visibilitychange", visibility);
    const timer = setInterval(() => { heartbeat(); if (visible()) void flush(); }, 30000);
    return () => {
      heartbeat(); stopped = true; clearInterval(timer); sub.remove();
      if (clickCapture === capture) clickCapture = null;
      if (Platform.OS === "web") document.removeEventListener("visibilitychange", visibility);
    };
  }, [screen, userId]);
}
