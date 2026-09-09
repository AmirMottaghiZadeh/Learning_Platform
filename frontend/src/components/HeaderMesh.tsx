import React from "react";
import { View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { useTheme } from "@/theme/ThemeProvider";

/** The accent "header mesh" backdrop used by auth / onboarding. */
export function HeaderMesh({ children }: { children: React.ReactNode }) {
  const { colors, isDark } = useTheme();
  return (
    <LinearGradient
      colors={isDark ? colors.headerMeshGradient : ["#0C4A43", "#0F5C52", "#14746A"]}
      start={{ x: 0.1, y: 0 }}
      end={{ x: 0.9, y: 1 }}
      style={{ flex: 1 }}
    >
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
