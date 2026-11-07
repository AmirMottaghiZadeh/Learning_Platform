import React from "react";
import { View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { StatusBar } from "expo-status-bar";

import { useBleedTop } from "@/components/AppShell";
import { useTheme } from "@/theme/ThemeProvider";

/** The accent "header mesh" backdrop used by auth / onboarding. At the top
 * of a screen (`bleedTop`) it also fills the strip under the status bar /
 * Dynamic Island, so the green runs to the top edge, and turns the status
 * bar's text light over it. */
export function HeaderMesh({ children, bleedTop = false }: { children: React.ReactNode; bleedTop?: boolean }) {
  const { colors, isDark } = useTheme();
  const top = useBleedTop(bleedTop);
  return (
    <LinearGradient
      colors={isDark ? colors.headerMeshGradient : ["#0C4A43", "#0F5C52", "#14746A"]}
      start={{ x: 0.1, y: 0 }}
      end={{ x: 0.9, y: 1 }}
      style={{ flex: 1, paddingTop: top }}
    >
      {bleedTop ? <StatusBar style="light" /> : null}
      <View
        pointerEvents="none"
        style={{
          position: "absolute",
          top: -60,
          right: -70,
          width: 220,
          height: 220,
          borderRadius: 110,
          borderWidth: 1,
          borderColor: "rgba(255,255,255,0.18)",
        }}
      />
      {children}
    </LinearGradient>
  );
}
