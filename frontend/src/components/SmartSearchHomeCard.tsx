import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Chevron } from "@/components/primitives/Chevron";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing, ThemeMode } from "@/theme/tokens";

const ACADEMY_COLORS: Record<ThemeMode, {
  surface: string;
  title: string;
  hint: string;
  iconBackground: string;
  accent: string;
}> = {
  light: { surface: "#FAF5E9", title: "#252B26", hint: "#5C5547", iconBackground: "#EAE0C9", accent: "#685327" },
  dark: { surface: "#332C23", title: "#FAEBD6", hint: "#D8C8AF", iconBackground: "#4C4030", accent: "#F2D29A" },
};

export function SmartSearchHomeCard({ onPress }: { onPress: () => void }) {
  const { mode } = useTheme();
  const colors = ACADEMY_COLORS[mode];
  const { row, isFa, t } = useLang();
  const label = t("resourceLookupSmart");
  const hint = isFa ? "پرسش بالینی از منابع مرجع" : "Ask a question about a clinical topic";
  return (
    <Pressable testID="home-smart-search" accessibilityRole="button" accessibilityLabel={label} accessibilityHint={hint}
      onPress={onPress} style={({ pressed }) => ({ opacity: pressed ? 0.76 : 1 })}>
      <Card style={{ flexDirection: row, alignItems: "center", gap: spacing.md, minHeight: 72, padding: spacing.md, backgroundColor: colors.surface }}>
        <View style={{ width: 42, height: 42, borderRadius: radius.input, backgroundColor: colors.iconBackground, alignItems: "center", justifyContent: "center" }}>
          <Svg width={23} height={23} viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth={1.7} aria-hidden>
            <Circle cx={10.5} cy={10.5} r={6.5} /><Path d="m16 16 4.5 4.5" strokeLinecap="round" />
          </Svg>
        </View>
        <View style={{ flex: 1 }}>
          <AppText weight="800" size={16} color={colors.title}>{label}</AppText>
          <AppText size={12} color={colors.hint}>{hint}</AppText>
        </View>
        <Chevron color={colors.accent} />
      </Card>
    </Pressable>
  );
}
