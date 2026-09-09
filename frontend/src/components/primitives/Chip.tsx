import React from "react";
import { Pressable } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { radius } from "@/theme/tokens";
import { AppText } from "./AppText";

type Props = {
  label: string;
  selected?: boolean;
  onPress?: () => void;
};

export function Chip({ label, selected, onPress }: Props) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={{
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: radius.chip,
        borderWidth: 1.5,
        borderColor: selected ? colors.accent : colors.trackBg,
        backgroundColor: selected ? colors.accent : colors.cardBg,
      }}
    >
      <AppText weight="700" size={13} color={selected ? colors.onAccent : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );
}
