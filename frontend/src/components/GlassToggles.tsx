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
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
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
        style={[chip, { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 }]}
      >
        <AppText weight="800" size={12} color="#fff">
          {t("langSwitch")}
        </AppText>
      </Pressable>
      <ThemeToggleButton size={34} />
    </View>
  );
}
