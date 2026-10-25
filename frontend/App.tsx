import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { StatusBar } from "expo-status-bar";
import React, { useEffect } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { CACHE_BUSTER, CACHE_MAX_AGE, queryClient, queryPersister } from "@/api/queryClient";
import { UpdatePrompt } from "@/components/UpdatePrompt";
import { LoadingState } from "@/components/primitives/LoadingState";
import { LanguageProvider, useLang } from "@/i18n/LanguageProvider";
import { Navigator } from "@/navigation/Navigator";
import { useOfflineBoot } from "@/offline/boot";
import { registerServiceWorker } from "@/offline/serviceWorker";
import { useAuth } from "@/store/auth";
import { ThemeProvider, useTheme } from "@/theme/ThemeProvider";
import { useAppFonts } from "@/theme/fonts";
import { TourProvider } from "@/tour/TourContext";
import { TourOverlay } from "@/tour/TourOverlay";

registerServiceWorker();

/** Status bar text dark on the light theme, light on the dark one -- "auto"
 * would follow the phone's dark mode, not the app's theme. */
function ThemedStatusBar() {
  const { isDark } = useTheme();
  return <StatusBar style={isDark ? "light" : "dark"} />;
}

function Gate() {
  const [fontsLoaded] = useAppFonts();
  const themeReady = useTheme().ready;
  const langReady = useLang().ready;
  const hydrate = useAuth((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);
  // Offline UpToDate/Lexicomp packages: resume downloads, renew licenses.
  useOfflineBoot();

  if (!fontsLoaded || !themeReady || !langReady) return <LoadingState />;
  return (
    <TourProvider>
      <Navigator />
      {/* The section's guided tour, over everything but system dialogs. */}
      <TourOverlay />
      {/* A newer published version: offered, or required, on opening. */}
      <UpdatePrompt />
    </TourProvider>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <LanguageProvider>
          {/* Answers already fetched survive closing the app: restored from
              device storage on start, shown at once, refreshed in the
              background only when stale (see api/queryClient). */}
          <PersistQueryClientProvider
            client={queryClient}
            persistOptions={{ persister: queryPersister, maxAge: CACHE_MAX_AGE, buster: CACHE_BUSTER }}
          >
            <ThemedStatusBar />
            <Gate />
          </PersistQueryClientProvider>
        </LanguageProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
