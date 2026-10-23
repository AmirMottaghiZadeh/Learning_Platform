import { useEffect } from "react";
import { AppState } from "react-native";

import { useAuth } from "@/store/auth";

import { DATASETS, bootOffline, renewLicense, resetOfflineBoot } from "./store";

/** Mounted once at the app root: starts the offline packages for whoever is
 * signed in (again after an account switch), and renews their licenses
 * whenever the app comes back to the foreground. */
export function useOfflineBoot() {
  const userId = useAuth((s) => (s.status === "signedIn" ? s.user?.id ?? null : null));

  useEffect(() => {
    if (userId == null) return;
    resetOfflineBoot();
    void bootOffline();
  }, [userId]);

  useEffect(() => {
    const sub = AppState.addEventListener("change", (state) => {
      if (state === "active") for (const dataset of DATASETS) void renewLicense(dataset);
    });
    return () => sub.remove();
  }, []);
}
