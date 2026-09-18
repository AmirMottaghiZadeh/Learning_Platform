import React from "react";
import { KeyboardAvoidingView, Platform, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useTheme } from "@/theme/ThemeProvider";
import { layout, radius } from "@/theme/tokens";
import { MeshBackground } from "./MeshBackground";

/**
 * The 430px framed shell from the design: a centred rounded card on a mesh
 * ground -- on wide web, where it reads as a phone mockup. On native (a
 * *real* phone, which already has its own physical rounded corners) that
 * same rounding + shadow + max-width instead clipped the app's own content
 * away from the four corners of the screen, showing the plain mesh
 * background through the gap. So the framed look is web-only; native
 * renders truly edge-to-edge.
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
  const isWeb = Platform.OS === "web";

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
            isWeb && { maxWidth: layout.appMaxWidth, borderRadius: radius.shell },
            isWeb && shadows.shell,
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
