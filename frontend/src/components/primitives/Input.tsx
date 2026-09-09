import React from "react";
import { TextInput, TextInputProps, View } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { radius } from "@/theme/tokens";

type Props = TextInputProps;

export function Input(props: Props) {
  const { colors } = useTheme();
  const { dir } = useLang();
  return (
    <View
      style={{
        height: 48,
        borderRadius: radius.input,
        backgroundColor: colors.inputBg,
        borderWidth: 1,
        borderColor: colors.trackBg,
        paddingHorizontal: 16,
        justifyContent: "center",
      }}
    >
      <TextInput
        placeholderTextColor={colors.muted}
        {...props}
        style={[
          {
            fontFamily: fontFamily("500"),
            fontSize: 15,
            color: colors.ink,
            textAlign: dir === "rtl" ? "right" : "left",
            writingDirection: dir,
            padding: 0,
          },
          props.style,
        ]}
      />
    </View>
  );
}
