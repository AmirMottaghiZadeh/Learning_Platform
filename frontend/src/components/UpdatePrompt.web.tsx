import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

// A tab or installed web app can stay open for days: look for a new deploy
// this often, and whenever it comes back into view.
const RECHECK_MS = 30 * 60 * 1000;
const BUNDLE = /\/_expo\/static\/js\/web\/[^"'?#]+\.js/g;

/** The content-hashed bundles the running page loaded. */
function loadedBundles(): string[] {
  return Array.from(document.querySelectorAll<HTMLScriptElement>("script[src]"))
    .map((script) => new URL(script.src).pathname)
    .filter((path) => path.match(BUNDLE))
    .sort();
}

/** The bundles the server's current index.html names -- fetched past every
 * cache, the service worker's included. Empty when it can't be read. */
async function deployedBundles(base: string): Promise<string[]> {
  try {
    const response = await fetch(`${base}/index.html`, { cache: "no-store" });
    if (!response.ok) return [];
    return [...new Set((await response.text()).match(BUNDLE) ?? [])].sort();
  } catch {
    return [];
  }
}

/** The web app's counterpart of the phone's update prompt: a deploy names
 * new bundles in index.html, and a page loaded before it keeps running the
 * old ones until reloaded. When the deployed page names other bundles than
 * the running one, a banner offers the reload. Production builds only --
 * the dev server's bundle isn't hashed. */
export function UpdatePrompt() {
  const [ready, setReady] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (__DEV__) return;
    const loaded = loadedBundles();
    if (!loaded.length) return;
    // The page is served from wherever its bundles' /_expo/ sits under.
    const base = loaded[0].slice(0, loaded[0].indexOf("/_expo/"));
    const check = async () => {
      const deployed = await deployedBundles(base);
      if (deployed.length && deployed.join() !== loaded.join()) setReady(true);
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") void check();
    };
    const timer = setInterval(check, RECHECK_MS);
    document.addEventListener("visibilitychange", onVisible);
    void check();
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  if (!ready || dismissed) return null;
  return <Banner onReload={() => window.location.reload()} onDismiss={() => setDismissed(true)} />;
}

function Banner({ onReload, onDismiss }: { onReload: () => void; onDismiss: () => void }) {
  const { colors, shadows } = useTheme();
  const { t, row } = useLang();
  const insets = useSafeAreaInsets();

  return (
    <View
      pointerEvents="box-none"
      style={{ position: "absolute", top: insets.top + 10, left: 12, right: 12, alignItems: "center" }}
    >
      <View
        accessibilityRole="alert"
        style={[
          {
            flexDirection: row,
            alignItems: "center",
            gap: 10,
            maxWidth: 440,
            width: "100%",
            backgroundColor: colors.cardBg,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: colors.border,
            paddingVertical: 8,
            paddingHorizontal: 14,
          },
          shadows.raised,
        ]}
      >
        <AppText weight="700" size={13} style={{ flex: 1 }}>
          {t("webUpdateReady")}
        </AppText>
        <Pressable
          onPress={onReload}
          accessibilityRole="button"
          style={({ pressed }) => ({
            minHeight: 36,
            justifyContent: "center",
            paddingHorizontal: 12,
            borderRadius: 10,
            backgroundColor: colors.accent,
            opacity: pressed ? 0.8 : 1,
          })}
        >
          <AppText weight="800" size={13} color={colors.onAccent}>
            {t("webUpdateReload")}
          </AppText>
        </Pressable>
        <Pressable
          onPress={onDismiss}
          accessibilityRole="button"
          accessibilityLabel={t("dismiss")}
          hitSlop={8}
          style={{ width: 36, height: 36, alignItems: "center", justifyContent: "center" }}
        >
          <AppText weight="800" size={18} muted>
            ×
          </AppText>
        </Pressable>
      </View>
    </View>
  );
}
