import React from "react";
import { ActivityIndicator, Pressable, StyleProp, ViewStyle } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { radius } from "@/theme/tokens";
import { AppText } from "./AppText";

type Variant = "primary" | "secondary" | "ghost";

type Props = {
  label: string;
  onPress?: () => void;
  variant?: Variant;
  disabled?: boolean;
  loading?: boolean;
  full?: boolean;
  style?: StyleProp<ViewStyle>;
};

export function Button({
  label,
  onPress,
  variant = "primary",
  disabled,
  loading,
  full = true,
  style,
}: Props) {
  const { colors, shadows } = useTheme();
  const isPrimary = variant === "primary";
  const isGhost = variant === "ghost";

  const bg = isPrimary ? colors.accent : isGhost ? "transparent" : colors.softBg;
  const fg = isPrimary ? colors.onAccent : colors.ink;

  return (
    <Pressable
      onPress={disabled || loading ? undefined : onPress}
      style={({ pressed }) => [
        {
          height: 52,
          borderRadius: radius.btn,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: bg,
          borderWidth: variant === "secondary" ? 1 : 0,
          borderColor: colors.trackBg,
          opacity: disabled ? 0.5 : 1,
          alignSelf: full ? "stretch" : "flex-start",
          paddingHorizontal: 22,
          transform: [{ scale: pressed ? 0.985 : 1 }],
        },
        isPrimary && shadows.glow,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={fg} />
      ) : (
        <AppText weight="800" size={15} color={fg}>
          {label}
        </AppText>
      )}
    </Pressable>
  );
}
