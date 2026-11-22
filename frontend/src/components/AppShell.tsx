import React, { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from "react";
import { KeyboardAvoidingView, Platform, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { useTheme } from "@/theme/ThemeProvider";

const TopInset = createContext<{ claim: () => () => void }>({ claim: () => () => undefined });

/** A full-bleed header can paint the top safe area itself. */
export function useBleedTop(enabled: boolean) {
  const { claim } = useContext(TopInset);
  const insets = useSafeAreaInsets();
  useLayoutEffect(() => (enabled ? claim() : undefined), [enabled, claim]);
  return enabled ? insets.top : 0;
}

export function AppShell({ children, padBottom = true }: { children: React.ReactNode; padBottom?: boolean }) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const [claims, setClaims] = useState(0);
  const claim = useCallback(() => {
    setClaims((n) => n + 1);
    return () => setClaims((n) => n - 1);
  }, []);
  const topInset = useMemo(() => ({ claim }), [claim]);

  return (
    <SafeAreaView edges={["left", "right"]} style={{ flex: 1, backgroundColor: colors.appBg }}>
      {claims === 0 ? <View style={{ height: insets.top }} /> : null}
      <KeyboardAvoidingView
        testID="app-shell"
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : Platform.OS === "android" ? "height" : undefined}
      >
        <TopInset.Provider value={topInset}>{children}</TopInset.Provider>
      </KeyboardAvoidingView>
      {padBottom ? <View style={{ height: insets.bottom }} /> : null}
    </SafeAreaView>
  );
}
