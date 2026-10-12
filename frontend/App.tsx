import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { StatusBar } from "expo-status-bar";
import React, { useEffect } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { CACHE_BUSTER, CACHE_MAX_AGE, queryClient, queryPersister } from "@/api/queryClient";
import { LoadingState } from "@/components/primitives/LoadingState";
import { LanguageProvider, useLang } from "@/i18n/LanguageProvider";
import { Navigator } from "@/navigation/Navigator";
import { useAuth } from "@/store/auth";
import { ThemeProvider, useTheme } from "@/theme/ThemeProvider";
import { useAppFonts } from "@/theme/fonts";

function Gate() {
  const [fontsLoaded] = useAppFonts();
  const themeReady = useTheme().ready;
  const langReady = useLang().ready;
  const hydrate = useAuth((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!fontsLoaded || !themeReady || !langReady) return <LoadingState />;
  return <Navigator />;
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
            <StatusBar style="auto" />
            <Gate />
          </PersistQueryClientProvider>
        </LanguageProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
