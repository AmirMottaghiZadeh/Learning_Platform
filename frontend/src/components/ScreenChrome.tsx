import React, { useState } from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle, G, Line, Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { HelpKey, HelpSheet } from "@/components/HelpSheet";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** Round soft button used across the in-app screen headers. */
export function ChromeButton({
  onPress,
  children,
  size = 30,
}: {
  onPress: () => void;
  children: React.ReactNode;
  size?: number;
}) {
  const { colors, shadows } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: colors.softBg,
          alignItems: "center",
          justifyContent: "center",
        },
        shadows.raisedSm,
      ]}
    >
      {children}
    </Pressable>
  );
}

/** Title row + theme / language toggles, matching the design's screen headers. */
export function ScreenChrome({
  title,
  onBack,
  help,
}: {
  title: string;
  onBack?: () => void;
  help?: HelpKey;
}) {
  const { colors } = useTheme();
  const { t, isFa, toggle: toggleLang } = useLang();
  const { toggle: toggleTheme, isDark } = useTheme();
  const [helpOpen, setHelpOpen] = useState(false);

  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 14,
      }}
    >
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10, flex: 1 }}>
        {onBack ? (
          <ChromeButton onPress={onBack}>
            <AppText weight="800" size={15} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
        ) : null}
        <AppText weight="800" size={17}>
          {title}
        </AppText>
      </View>
      <View style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
        {help ? (
          <ChromeButton onPress={() => setHelpOpen(true)}>
            <AppText weight="800" size={13} color={colors.accent}>
              ?
            </AppText>
          </ChromeButton>
        ) : null}
        <ChromeButton onPress={toggleTheme}>
          <Svg width={14} height={14} viewBox="0 0 24 24">
            {isDark ? (
              <>
                <Circle cx={12} cy={12} r={5} fill={colors.accent} />
                <G stroke={colors.accent} strokeWidth={2} strokeLinecap="round">
                  <Line x1={12} y1={1} x2={12} y2={3} />
                  <Line x1={12} y1={21} x2={12} y2={23} />
                  <Line x1={1} y1={12} x2={3} y2={12} />
                  <Line x1={21} y1={12} x2={23} y2={12} />
                </G>
              </>
            ) : (
              <Path d="M21 12.5A8.5 8.5 0 1111.5 3 7 7 0 0021 12.5z" fill={colors.accent} />
            )}
          </Svg>
        </ChromeButton>
        <Pressable
          onPress={toggleLang}
          style={{
            backgroundColor: colors.softBg,
            borderRadius: 999,
            paddingHorizontal: 10,
            paddingVertical: 6,
          }}
        >
          <AppText weight="800" size={12} color={colors.accent}>
            {t("langSwitch")}
          </AppText>
        </Pressable>
      </View>
      {help ? (
        <HelpSheet helpKey={helpOpen ? help : null} onClose={() => setHelpOpen(false)} />
      ) : null}
    </View>
  );
}
