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
  const { colors } = useTheme();
  const isPrimary = variant === "primary";
  const isGhost = variant === "ghost";

  const bg = isPrimary ? colors.accent : isGhost ? "transparent" : colors.softBg;
  const fg = isPrimary ? colors.onAccent : colors.ink;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!disabled || !!loading, busy: !!loading }}
      disabled={!!disabled || !!loading}
      onPress={onPress}
      style={({ pressed }) => [
        {
          height: 52,
          borderRadius: radius.btn,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: bg,
          borderWidth: variant === "secondary" ? 1 : 0,
          borderColor: colors.trackBg,
          opacity: disabled ? 0.5 : pressed ? 0.82 : 1,
          alignSelf: full ? "stretch" : "flex-start",
          paddingHorizontal: 22,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={fg} />
      ) : (
        <AppText weight="700" size={15} color={fg}>
          {label}
        </AppText>
      )}
    </Pressable>
  );
}
