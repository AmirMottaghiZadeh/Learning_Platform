import React from "react";
import { View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { useBleedTop } from "@/components/AppShell";
import { useTheme } from "@/theme/ThemeProvider";

export function HeaderMesh({ children, bleedTop = false, testID }: {
  children: React.ReactNode;
  bleedTop?: boolean;
  testID?: string;
}) {
  const { colors } = useTheme();
  const top = useBleedTop(bleedTop);

  return (
    <View testID={testID} style={{ flex: 1, paddingTop: top, backgroundColor: colors.headerMesh }}>
      {bleedTop ? <StatusBar style="light" /> : null}
      {children}
    </View>
  );
}
