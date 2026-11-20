import React from "react";
import { View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { StatusBar } from "expo-status-bar";

import { useBleedTop } from "@/components/AppShell";
import { useTheme } from "@/theme/ThemeProvider";

/** Fills the status-bar inset when the header bleeds to the top. */
export function HeaderMesh({ children, bleedTop = false, gradient = false }: {
  children: React.ReactNode; bleedTop?: boolean; gradient?: boolean;
}) {
  const { colors, isDark } = useTheme();
  const top = useBleedTop(bleedTop);
  const status = bleedTop ? <StatusBar style="light" /> : null;

  if (!gradient) {
    return (
      <View style={{ flex: 1, paddingTop: top, backgroundColor: colors.headerMesh }}>
        {status}
        {children}
      </View>
    );
  }

  return (
    <LinearGradient
      colors={isDark ? colors.headerMeshGradient : ["#0C4A43", "#0F5C52", "#14746A"]}
      start={{ x: 0.1, y: 0 }}
      end={{ x: 0.9, y: 1 }}
      style={{ flex: 1, paddingTop: top }}
    >
      {status}
      <View pointerEvents="none" style={{
        position: "absolute", top: -60, right: -70, width: 220, height: 220,
        borderRadius: 110, borderWidth: 1, borderColor: "rgba(255,255,255,0.18)",
      }} />
      {children}
    </LinearGradient>
  );
}
