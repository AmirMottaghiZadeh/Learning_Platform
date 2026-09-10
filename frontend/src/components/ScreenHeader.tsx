import React from "react";
import { Pressable, View } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { AppText } from "./primitives/AppText";

export function ScreenHeader({
  title,
  subtitle,
  back,
}: {
  title: string;
  subtitle?: string;
  back?: boolean;
}) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const goBack = useNav((s) => s.goBack);

  return (
    <View style={{ flexDirection: row, alignItems: "center", gap: 10, marginBottom: 14 }}>
      {back ? (
        <Pressable
          onPress={goBack}
          style={{
            width: 34,
            height: 34,
            borderRadius: 10,
            backgroundColor: colors.softBg,
            borderWidth: 1,
            borderColor: colors.trackBg,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AppText weight="800" size={16} color={colors.ink}>
            {isFa ? "›" : "‹"}
          </AppText>
        </Pressable>
      ) : null}
      <View style={{ flex: 1 }}>
        <AppText weight="800" size={20}>
          {title}
        </AppText>
        {subtitle ? (
          <AppText muted weight="600" size={12} style={{ marginTop: 2 }}>
            {subtitle}
          </AppText>
        ) : null}
      </View>
    </View>
  );
}
