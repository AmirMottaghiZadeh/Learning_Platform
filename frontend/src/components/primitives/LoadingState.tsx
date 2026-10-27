import React from "react";
import { ActivityIndicator, View } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { AppText } from "./AppText";

export function LoadingState({ label }: { label?: string }) {
  const { colors } = useTheme();
  return (
    <View
      style={{
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: colors.appBg,
        gap: 12,
      }}
    >
      <ActivityIndicator size="large" color={colors.accent} />
      {label ? (
        <AppText muted size={13} weight="600">
          {label}
        </AppText>
      ) : null}
    </View>
  );
}
