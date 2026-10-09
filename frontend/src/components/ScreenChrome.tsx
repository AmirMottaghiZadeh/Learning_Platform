import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { HelpKey, HelpSheet } from "@/components/HelpSheet";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
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
  const { t, isFa, row, toggle: toggleLang } = useLang();
  const [helpOpen, setHelpOpen] = useState(false);

  return (
    <View
      style={{
        flexDirection: row,
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 14,
      }}
    >
      <View style={{ flexDirection: row, alignItems: "center", gap: 10, flex: 1 }}>
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
      <View style={{ flexDirection: row, gap: 8, alignItems: "center" }}>
        {help ? (
          <ChromeButton onPress={() => setHelpOpen(true)}>
            <AppText weight="800" size={13} color={colors.accent}>
              ?
            </AppText>
          </ChromeButton>
        ) : null}
        <ThemeToggleButton variant="soft" size={30} />
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
