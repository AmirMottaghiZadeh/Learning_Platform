import React from "react";
import { View } from "react-native";

import { TextInput } from "@/components/primitives/TextInput";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

/** The one search field the reference browse screens share. It sits above the
 * topics and the list, so it is the first thing a reader reaches. */
export function BrowseSearch({
  value,
  onChangeText,
  placeholder,
  busy = false,
}: {
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  busy?: boolean;
}) {
  const { colors } = useTheme();
  const { row } = useLang();
  return (
    <View
      style={{
        flexDirection: row,
        alignItems: "center",
        gap: 8,
        backgroundColor: colors.inputBg,
        boxShadow: colors.cardShadow,
        borderRadius: 14,
        paddingHorizontal: 14,
        paddingVertical: 12,
      }}
    >
      <AppText muted>⌕</AppText>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        accessibilityLabel={placeholder}
        style={{
          flex: 1,
          fontFamily: fontFamily("600"),
          fontSize: 13,
          color: colors.ink,
          textAlign: "left",
          writingDirection: "ltr",
          padding: 0,
        }}
      />
      {busy ? <AppText muted size={12}>…</AppText> : null}
    </View>
  );
}
