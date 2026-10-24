/**
 * One "back" for the whole app, shared by Android's hardware/gesture Back
 * and the browser's back (the button, and iOS Safari's / a home-screen web
 * app's edge swipe -- see WebBackGuard in Navigator).
 *
 * A step back is, in order:
 *  1. the innermost screen-level interceptor, if one is active -- a screen
 *     with its own internal levels (flashcard category -> topic -> deck, a
 *     running quiz, a calculator's next question, an open sheet) steps back
 *     through those first;
 *  2. the in-app navigation history;
 *  3. from another tab's root, Home.
 * Only when none of those applies is the app at its root, and Back leaves it.
 */
import { useEffect, useRef } from "react";

import { useNav } from "@/store/nav";

type Interceptor = { id: number; handle: () => void };

const interceptors: Interceptor[] = [];
const listeners = new Set<() => void>();
let nextId = 0;

function notify() {
  listeners.forEach((listener) => listener());
}

// Navigation changes can make "can go back" flip, as can interceptors coming
// and going; listeners (the web history guard) re-check on either.
useNav.subscribe(notify);

/** Called whenever canGoBack() may have changed. Returns an unsubscribe. */
export function subscribeBackState(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Whether a Back press stays inside the app. */
export function canGoBack(): boolean {
  const { screen, history } = useNav.getState();
  return interceptors.length > 0 || history.length > 0 || screen !== "dashboard";
}

/** Takes one step back inside the app. Returns false at the app's root,
 * where Back should leave it instead. */
export function goBackInApp(): boolean {
  const innermost = interceptors[interceptors.length - 1];
  if (innermost) {
    innermost.handle();
    return true;
  }
  const { screen, history, goBack, setTab } = useNav.getState();
  if (history.length > 0) {
    goBack();
    return true;
  }
  if (screen !== "dashboard") {
    setTab("dashboard");
    return true;
  }
  return false;
}

/** While `active`, a Back press calls `handle` instead of leaving the screen
 * -- for a screen's own inner levels (or an open sheet). The most recently
 * activated interceptor goes first. */
export function useBackInterceptor(active: boolean, handle: () => void) {
  const latest = useRef(handle);
  latest.current = handle;

  useEffect(() => {
    if (!active) return;
    const entry: Interceptor = { id: nextId++, handle: () => latest.current() };
    interceptors.push(entry);
    notify();
    return () => {
      const i = interceptors.findIndex((it) => it.id === entry.id);
      if (i >= 0) interceptors.splice(i, 1);
      notify();
    };
  }, [active]);
}

/** The browser's back -- the button, and the edge-swipe in iOS Safari or a
 * home-screen web app, which has no other back control -- as an in-app step
 * back instead of leaving the site. The app navigates without touching the
 * URL, so it keeps one extra "guard" history entry whenever it can go back:
 * the browser's back pops the guard, and the app takes a step back and
 * re-arms it if there's still somewhere to go. At the app's root no guard is
 * left, so back leaves the site as usual. Returns an uninstall function. */
export function installWebBackGuard(win: Pick<Window, "history" | "addEventListener" | "removeEventListener">) {
  let armed = false;
  // Our own history.back() (to drop a guard no longer needed) also fires
  // popstate; these are skipped rather than taken as the user's back.
  let selfPops = 0;

  const sync = () => {
    const want = canGoBack();
    if (want && !armed) {
      win.history.pushState({ pharmentaBack: true }, "");
      armed = true;
    } else if (!want && armed) {
      armed = false;
      selfPops++;
      win.history.back();
    }
  };
  const onPopState = () => {
    if (selfPops > 0) {
      selfPops--;
      return;
    }
    if (!armed) return; // past the app's own entries: a real leave
    armed = false;
    goBackInApp();
    sync();
  };

  win.addEventListener("popstate", onPopState);
  const unsubscribe = subscribeBackState(sync);
  sync();
  return () => {
    win.removeEventListener("popstate", onPopState);
    unsubscribe();
  };
}
