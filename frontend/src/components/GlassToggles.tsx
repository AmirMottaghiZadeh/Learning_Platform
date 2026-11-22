import React from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { useLang } from "@/i18n/LanguageProvider";

/** The frosted lang + theme toggles pinned to the top of the auth screens. */
export function GlassToggles() {
  const { t, row, toggle: toggleLang } = useLang();
  const chip = {
    backgroundColor: "rgba(255,255,255,0.16)",
  } as const;

  return (
    <View
      style={{
        flexDirection: row,
        justifyContent: "space-between",
        paddingHorizontal: 18,
        paddingTop: 8,
      }}
    >
      <Pressable
        onPress={toggleLang}
        accessibilityRole="button"
        accessibilityLabel={t("langSwitch")}
        style={[chip, { borderRadius: 12, minHeight: 44, minWidth: 44, justifyContent: "center", alignItems: "center" }]}
      >
        <AppText weight="800" size={12} color="#fff">
          {t("langSwitch")}
        </AppText>
      </Pressable>
      <ThemeToggleButton />
    </View>
  );
}
