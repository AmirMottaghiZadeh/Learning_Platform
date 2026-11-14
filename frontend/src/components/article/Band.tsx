import React from "react";
import { Pressable, StyleProp, View, ViewStyle } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** Colours of the teal header band the guideline/disease article pages use
 * (design option 3): the brand teal with white type in light mode, the dark
 * theme's own header tone in dark mode. */
export function useBandColors() {
  const { colors, isDark } = useTheme();
  return {
    bg: colors.headerMesh,
    ink: isDark ? colors.ink : "#FFFFFF",
    sub: isDark ? colors.muted : "#CFE6DD",
    eyebrow: isDark ? colors.accent : "#A9D8C4",
    chip: isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.1)",
    button: isDark ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.14)",
    outline: isDark ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.35)",
  };
}

/** Square-ish translucent button on the band. */
export function BandButton({
  onPress,
  children,
  label,
  size = 32,
  style,
}: {
  onPress: () => void;
  children: React.ReactNode;
  label: string;
  size?: number;
  style?: StyleProp<ViewStyle>;
}) {
  const band = useBandColors();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      hitSlop={6}
      style={[
        {
          width: size,
          height: size,
          borderRadius: 10,
          backgroundColor: band.button,
          alignItems: "center",
          justifyContent: "center",
        },
        style,
      ]}
    >
      {children}
    </Pressable>
  );
}

/** The EN/FA switch, outlined to sit on the band. */
export function BandLangToggle() {
  const band = useBandColors();
  const { t, toggle } = useLang();
  return (
    <Pressable
      onPress={toggle}
      style={{ borderWidth: 1, borderColor: band.outline, borderRadius: 8, paddingHorizontal: 9, paddingVertical: 4 }}
    >
      <AppText weight="800" size={11.5} color={band.ink}>
        {t("langSwitch")}
      </AppText>
    </Pressable>
  );
}

/** The back chevron, pointing the way "back" reads in the current language. */
export function BackGlyph({ color }: { color: string }) {
  const { isFa } = useLang();
  return (
    <AppText weight="800" size={16} color={color} center style={{ lineHeight: 20 }}>
      {isFa ? "›" : "‹"}
    </AppText>
  );
}

export function BandSpacer() {
  return <View style={{ flex: 1 }} />;
}
