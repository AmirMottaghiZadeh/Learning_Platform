import { QueryClientProvider } from "@tanstack/react-query";
import { StatusBar } from "expo-status-bar";
import React, { useEffect } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { queryClient } from "@/api/queryClient";
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
          <QueryClientProvider client={queryClient}>
            <StatusBar style="auto" />
            <Gate />
          </QueryClientProvider>
        </LanguageProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
