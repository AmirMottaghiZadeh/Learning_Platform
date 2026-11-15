import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { radius as radii, spacing } from "@/theme/tokens";

/** Selected home design 1: a reference card using the app's usual surfaces. */
export function SmartSearchHomeCard({ onPress }: { onPress: () => void }) {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  return <Pressable testID="home-smart-search" accessibilityRole="button" onPress={onPress}
    accessibilityLabel={isFa ? "سرچ هوشمند؛ پرسش از منابع معتبر بالینی" : "Smart search: ask trusted clinical references"}
    style={{ marginBottom: 18, padding: spacing.lg, borderRadius: radii.card, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.cardBg, gap: 8 }}>
    <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: spacing.md }}>
      <AppText weight="800" size={18}>{isFa ? "سرچ هوشمند" : "Smart search"}</AppText>
      <Svg width={27} height={27} viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth={1.7} accessibilityElementsHidden>
        <Circle cx={10.5} cy={10.5} r={6.5} /><Path d="m16 16 4.5 4.5" strokeLinecap="round" />
      </Svg>
    </View>
    <AppText muted size={12}>{isFa ? "پرسش از منابع معتبر بالینی" : "Ask trusted clinical references"}</AppText>
    <View style={{ flexDirection: row, alignItems: "center", gap: spacing.md, backgroundColor: colors.softBg, borderRadius: radii.input, padding: spacing.md, minHeight: 48, marginTop: 8 }}>
      <AppText muted size={13} style={{ flex: 1 }}>{isFa ? "سؤال بالینی خود را بپرسید" : "Ask your clinical question"}</AppText>
      <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth={1.7} accessibilityElementsHidden>
        <Path d={isFa ? "M20 12H4m6-6-6 6 6 6" : "M4 12h16m-6-6 6 6-6 6"} strokeLinecap="round" strokeLinejoin="round" />
      </Svg>
    </View>
  </Pressable>;
}
