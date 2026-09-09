import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle, G, Line, Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** The frosted lang + theme toggles pinned to the top of the auth screens. */
export function GlassToggles() {
  const { t, toggle: toggleLang } = useLang();
  const { toggle: toggleTheme, isDark } = useTheme();
  const chip = {
    backgroundColor: "rgba(255,255,255,0.16)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
  } as const;

  return (
    <View
      style={{
        flexDirection: "row",
        justifyContent: "space-between",
        paddingHorizontal: 18,
        paddingTop: 8,
      }}
    >
      <Pressable
        onPress={toggleLang}
        style={[chip, { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 }]}
      >
        <AppText weight="800" size={12} color="#fff">
          {t("langSwitch")}
        </AppText>
      </Pressable>
      <Pressable
        onPress={toggleTheme}
        style={[
          chip,
          { width: 34, height: 34, borderRadius: 17, alignItems: "center", justifyContent: "center" },
        ]}
      >
        <Svg width={16} height={16} viewBox="0 0 24 24">
          {isDark ? (
            <>
              <Circle cx={12} cy={12} r={5} fill="#fff" />
              <G stroke="#fff" strokeWidth={2} strokeLinecap="round">
                <Line x1={12} y1={1} x2={12} y2={3} />
                <Line x1={12} y1={21} x2={12} y2={23} />
                <Line x1={1} y1={12} x2={3} y2={12} />
                <Line x1={21} y1={12} x2={23} y2={12} />
              </G>
            </>
          ) : (
            <Path d="M21 12.5A8.5 8.5 0 1111.5 3 7 7 0 0021 12.5z" fill="#fff" />
          )}
        </Svg>
      </Pressable>
    </View>
  );
}
