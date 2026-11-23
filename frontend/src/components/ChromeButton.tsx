import React from "react";
import { Pressable } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";

export function ChromeButton({
  onPress,
  children,
  size = 44,
  variant = "soft",
  accessibilityLabel,
}: {
  onPress: () => void;
  children: React.ReactNode;
  size?: number;
  variant?: "soft" | "chip" | "control";
  accessibilityLabel?: string;
}) {
  const { colors } = useTheme();
  const backgroundColor = variant === "chip" ? colors.headerControlBg
    : variant === "control" ? colors.chromeControlBg : colors.softBg;

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      hitSlop={Math.max(0, (44 - size) / 2)}
      style={({ pressed }) => ({
        opacity: pressed ? 0.8 : 1,
        width: size,
        height: size,
        borderRadius: 12,
        backgroundColor,
        alignItems: "center",
        justifyContent: "center",
      })}
    >
      {children}
    </Pressable>
  );
}
