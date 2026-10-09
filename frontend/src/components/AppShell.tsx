import React from "react";
import { KeyboardAvoidingView, Platform, useWindowDimensions, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

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
 * mockup frame.
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
export function AppShell({ children }: { children: React.ReactNode }) {
  const { colors, shadows } = useTheme();
  const { width } = useWindowDimensions();
  const showMockupFrame = Platform.OS === "web" && width > layout.appMaxWidth;

  return (
    <View style={{ flex: 1, backgroundColor: colors.meshBg }}>
      <MeshBackground />
      <SafeAreaView style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
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
          <KeyboardAvoidingView
            style={{ flex: 1 }}
            behavior={
              Platform.OS === "ios" ? "padding" : Platform.OS === "android" ? "height" : undefined
            }
          >
            {children}
          </KeyboardAvoidingView>
        </View>
      </SafeAreaView>
    </View>
  );
}
