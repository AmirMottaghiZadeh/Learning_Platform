import React, { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from "react";
import { KeyboardAvoidingView, Platform, useWindowDimensions, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { useTheme } from "@/theme/ThemeProvider";
import { layout, radius } from "@/theme/tokens";
import { MeshBackground } from "./MeshBackground";

/**
 * The 430px framed shell from the design: a centred rounded card on a mesh
 * ground -- a phone mockup, for a DESKTOP browser window wider than the app
 * itself, where that extra space would otherwise just be empty mesh on
 * either side. On a real phone (native, which already has its own physical
 * rounded corners) that same rounding + shadow + max-width instead clipped
 * the app's own content away from the four corners of the screen. The same
 * is true of a phone's own *browser* or a PWA shell: `Platform.OS` reports
 * "web" there too, but the viewport is already phone-width, so framing it
 * again produced the reported "phone inside a phone" look, rounded corners
 * and all, instead of filling the real screen. Gating on actual viewport
 * width (not just the web/native platform split) makes both cases render
 * truly edge-to-edge, and only a genuinely wider desktop window gets the
 * mockup frame. The cut-off is a tablet width (mockupFrameMinWidth), not
 * the 430px card itself: phones wider than 430 exist (iPhone 16/17 Pro Max
 * at 440, Android phones with a smaller display-size setting at 450-500),
 * and framing those left rounded corners and a sliver of mesh at both sides.
 *
 * Every screen renders inside this one component (Navigator wraps the whole
 * authenticated app in it, and AuthScreen/OnboardingScreen each use it
 * directly), so the keyboard-avoidance wrapper belongs here once rather than
 * repeated per screen: without it, a focused input below the keyboard's
 * top edge is simply hidden behind it while typing, since neither platform
 * shrinks the app's own layout for a software keyboard on its own -- iOS
 * needs "padding", Android needs "height" (web's KeyboardAvoidingView is a
 * no-op, so `undefined` there changes nothing).
 */
const TopInset = createContext<{ claim: () => () => void }>({ claim: () => () => undefined });

/**
 * For a header that paints the strip under the status bar / Dynamic Island
 * itself (the green HeaderMesh at the top of Home, Profile and sign-in):
 * while `enabled`, AppShell leaves that strip to it, and this returns how
 * tall it is so the header can pad its content below it.
 */
export function useBleedTop(enabled: boolean) {
  const { claim } = useContext(TopInset);
  const insets = useSafeAreaInsets();
  useLayoutEffect(() => (enabled ? claim() : undefined), [enabled, claim]);
  return enabled ? insets.top : 0;
}

/**
 * The safe areas -- the strip under the status bar or Dynamic Island, and
 * the one over the home indicator -- are filled by the app itself, not left
 * to show the mesh ground behind it (which read as a stray band above the
 * header and below the tab bar on an iPhone). The top strip is the screen's
 * own background unless a header claims it (useBleedTop); the bottom one is
 * the screen's background too, or, with `padBottom={false}`, left to the
 * BottomNav, which grows into it.
 */
export function AppShell({ children, padBottom = true }: { children: React.ReactNode; padBottom?: boolean }) {
  const { colors, shadows } = useTheme();
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const showMockupFrame = Platform.OS === "web" && width >= layout.mockupFrameMinWidth;
  const [claims, setClaims] = useState(0);
  const claim = useCallback(() => {
    setClaims((n) => n + 1);
    return () => setClaims((n) => n - 1);
  }, []);
  const topInset = useMemo(() => ({ claim }), [claim]);

  return (
    <View style={{ flex: 1, backgroundColor: colors.meshBg }}>
      <MeshBackground />
      <SafeAreaView edges={["left", "right"]} style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <View
          style={[
            {
              flex: 1,
              width: "100%",
              backgroundColor: colors.appBg,
              overflow: "hidden",
            },
            showMockupFrame && { maxWidth: layout.appMaxWidth, borderRadius: radius.shell },
            showMockupFrame && shadows.shell,
          ]}
        >
          {claims === 0 ? <View style={{ height: insets.top }} /> : null}
          <KeyboardAvoidingView
            style={{ flex: 1 }}
            behavior={
              Platform.OS === "ios" ? "padding" : Platform.OS === "android" ? "height" : undefined
            }
          >
            <TopInset.Provider value={topInset}>{children}</TopInset.Provider>
          </KeyboardAvoidingView>
          {padBottom ? <View style={{ height: insets.bottom }} /> : null}
        </View>
      </SafeAreaView>
    </View>
  );
}
