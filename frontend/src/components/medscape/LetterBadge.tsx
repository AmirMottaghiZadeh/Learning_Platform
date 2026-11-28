import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

/** The A-Z section marker. A dashed accent square with the letter inside, so
 * a group header never reads as one more article row: article rows are solid
 * white surfaces, this is outlined and set off to the side. */
export function LetterBadge({ letter, countLabel }: { letter: string; countLabel: string }) {
  const { colors } = useTheme();
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flex: 1 }}>
      <View
        style={{
          width: 24,
          height: 24,
          borderRadius: 7,
          borderWidth: 1.5,
          borderStyle: "dashed",
          borderColor: colors.accent,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: colors.appBg,
        }}
      >
        <AppText weight="800" size={11} color={colors.accent} style={{ fontFamily: fontFamily("800") }}>
          {letter}
        </AppText>
      </View>
      <AppText weight="700" size={10.5} color={colors.muted}>
        {countLabel}
      </AppText>
      <View style={{ flex: 1, height: 1, backgroundColor: colors.trackBg, marginStart: 2 }} />
    </View>
  );
}
