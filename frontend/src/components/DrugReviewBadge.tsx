import React from "react";
import { View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** Editorial review of the whole drug, independent of a learner's read tick. */
export function DrugReviewBadge({ reviewed }: { reviewed: boolean }) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const color = reviewed ? colors.accent : colors.denyLabel;
  const label = reviewed ? (isFa ? "بازبینی شده" : "Reviewed") : (isFa ? "بازبینی نشده" : "Not reviewed");
  return (
    <View accessible accessibilityLabel={label} style={{ flexDirection: row, alignItems: "center", alignSelf: "flex-start", gap: 5,
      paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8,
      backgroundColor: reviewed ? colors.leitnerActiveBg : colors.denyBg }}>
      <Svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        {reviewed ? <Path d="m5 12 4 4L19 6" /> : <><Path d="M12 3 2 21h20L12 3Z" /><Path d="M12 9v4m0 4h.01" /></>}
      </Svg>
      <AppText size={11.5} weight="700" color={color}>{label}</AppText>
    </View>
  );
}
