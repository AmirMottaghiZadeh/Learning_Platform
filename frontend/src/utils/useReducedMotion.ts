import { useEffect, useState } from "react";
import { AccessibilityInfo, Platform } from "react-native";

function webPreference() {
  return typeof window === "undefined" ? null : window.matchMedia?.("(prefers-reduced-motion: reduce)") ?? null;
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => Platform.OS !== "web" || (webPreference()?.matches ?? true));

  useEffect(() => {
    if (Platform.OS === "web") {
      const media = webPreference();
      if (!media) return;
      const update = () => setReduced(media.matches);
      update();
      media.addEventListener("change", update);
      return () => media.removeEventListener("change", update);
    }

    let current = true;
    let changed = false;
    const subscription = AccessibilityInfo.addEventListener("reduceMotionChanged", (value) => {
      changed = true;
      setReduced(value);
    });
    void AccessibilityInfo.isReduceMotionEnabled().then((value) => {
      if (current && !changed) setReduced(value);
    }).catch(() => undefined);
    return () => { current = false; subscription.remove(); };
  }, []);

  return reduced;
}
