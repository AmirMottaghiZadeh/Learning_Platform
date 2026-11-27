import React, { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from "react";
import { KeyboardAvoidingView, Platform, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { useTheme } from "@/theme/ThemeProvider";

const TopInset = createContext<{ claim: () => () => void }>({ claim: () => () => undefined });

/** A full-bleed header can paint the top safe area itself. */
export function useBleedTop(enabled: boolean) {
  const { claim } = useContext(TopInset);
  const insets = useSafeAreaInsets();
  // The shell draws its own top spacer until this component claims it. Return
  // the inset only after the claim is applied, so no frame counts the safe
  // area twice -- that double inset made the top of the lesson list jump on a
  // new user's first entry.
  const [claimed, setClaimed] = useState(false);
  useLayoutEffect(() => {
    if (!enabled) {
      setClaimed(false);
      return undefined;
    }
    const release = claim();
    setClaimed(true);
    return release;
  }, [enabled, claim]);
  return enabled && claimed ? insets.top : 0;
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
