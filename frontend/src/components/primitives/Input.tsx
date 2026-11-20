import React, { useState } from "react";
import { TextInputProps, View } from "react-native";
import { TextInput } from "@/components/primitives/TextInput";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { radius } from "@/theme/tokens";

type Props = TextInputProps;

export function Input(props: Props) {
  const { colors } = useTheme();
  const { dir } = useLang();
  const [focused, setFocused] = useState(false);
  return (
    <View
      style={{
        height: 48,
        borderRadius: radius.input,
        backgroundColor: colors.inputBg,
        borderWidth: focused ? 2 : 1,
        borderColor: focused ? colors.accent : colors.trackBg,
        paddingHorizontal: 16,
        justifyContent: "center",
      }}
    >
      <TextInput
        placeholderTextColor={colors.muted}
        {...props}
        onFocus={(event) => { setFocused(true); props.onFocus?.(event); }}
        onBlur={(event) => { setFocused(false); props.onBlur?.(event); }}
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
