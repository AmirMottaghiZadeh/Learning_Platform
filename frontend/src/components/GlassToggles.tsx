import React from "react";
import { View } from "react-native";

import { LangToggleButton } from "@/components/ScreenChrome";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { useLang } from "@/i18n/LanguageProvider";

export function GlassToggles() {
  const { row } = useLang();

  return (
    <View
      style={{
        flexDirection: row,
        justifyContent: "space-between",
        paddingHorizontal: 18,
        paddingTop: 8,
      }}
    >
      <LangToggleButton variant="chip" />
      <ThemeToggleButton />
    </View>
  );
}
