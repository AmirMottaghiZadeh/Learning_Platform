import type { InstallOutcome, InstallState } from "./types";

type InstallPrompt = Event & {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};
const INSTALLED_KEY = "pharmenta:pwa-installed";
const listeners = new Set<() => void>();
let deferred: InstallPrompt | null = null;
let initialized = false;
let state: InstallState = { environment: "browser", canPrompt: false, manual: "browser", busy: false };

function update(next: Partial<InstallState>) {
  state = { ...state, ...next };
  listeners.forEach((listener) => listener());
}
function rememberInstalled() {
  try { window.localStorage.setItem(INSTALLED_KEY, "1"); } catch { /* private browsing */ }
  deferred = null;
  update({ environment: "standalone", canPrompt: false, busy: false });
}

/** Capture the one-shot event at app startup, before login/home mounts. */
export function initializeInstall() {
  if (initialized || typeof window === "undefined") return;
  initialized = true;
  const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  update({ manual: ios ? "ios" : "browser" });
  const standalone = window.matchMedia("(display-mode: standalone)");
  if (standalone.matches || (navigator as Navigator & { standalone?: boolean }).standalone) rememberInstalled();
  else {
    try { if (window.localStorage.getItem(INSTALLED_KEY) === "1") update({ environment: "standalone" }); } catch { /* storage unavailable */ }
  }
  standalone.addEventListener("change", (event) => { if (event.matches) rememberInstalled(); });
  window.addEventListener("appinstalled", rememberInstalled);
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferred = event as InstallPrompt;
    // A fresh browser offer is better evidence than a past installation:
    // the user may have uninstalled the PWA since their last visit.
    try { window.localStorage.removeItem(INSTALLED_KEY); } catch { /* storage unavailable */ }
    update({ environment: "browser", canPrompt: true });
  });
}
export const getInstallState = () => state;
export function subscribeInstall(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** Call directly from the click handler: browsers require a user gesture. */
export async function requestInstall(): Promise<InstallOutcome> {
  if (!deferred || state.busy) return "manual";
  const prompt = deferred;
  deferred = null;
  update({ canPrompt: false, busy: true });
  try {
    await prompt.prompt();
    return (await prompt.userChoice).outcome;
  } catch {
    return "error";
  } finally {
    update({ busy: false });
  }
}
