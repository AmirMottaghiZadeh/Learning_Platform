import React from "react";
import { View } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";

/**
 * The design's soft mesh backdrop. A flat wash plus two faint accent blooms —
 * enough to read as the design without pulling in SVG here.
 */
export function MeshBackground() {
  const { colors } = useTheme();
  return (
    <View
      pointerEvents="none"
      style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, overflow: "hidden" }}
    >
      <View style={{ flex: 1, backgroundColor: colors.meshBg }} />
      <Bloom color={colors.accent} top={-120} left={-80} />
      <Bloom color={colors.accent2} bottom={-140} right={-100} />
    </View>
  );
}

function Bloom({
  color,
  top,
  left,
  right,
  bottom,
}: {
  color: string;
  top?: number;
  left?: number;
  right?: number;
  bottom?: number;
}) {
  return (
    <View
      style={{
        position: "absolute",
        top,
        left,
        right,
        bottom,
        width: 320,
        height: 320,
        borderRadius: 160,
        backgroundColor: color,
        opacity: 0.06,
      }}
    />
  );
}
