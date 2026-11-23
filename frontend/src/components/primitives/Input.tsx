import React, { useContext, useState } from "react";
import { Platform, TextInputProps, View } from "react-native";
import { TextInput } from "@/components/primitives/TextInput";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { radius } from "@/theme/tokens";
import { SquircleView } from "./SquircleView";
import { CardSurface } from "./Card";
import { AppText } from "./AppText";

type Props = TextInputProps & { label?: string; auth?: boolean };

export function Input({ label, auth, ...props }: Props) {
  const { colors, isDark, shadows } = useTheme();
  const nested = useContext(CardSurface);
  const { dir } = useLang();
  const [focused, setFocused] = useState(false);
  const field = (
    <SquircleView
      style={[!nested && shadows.surface, {
        minHeight: auth ? 54 : 48,
        borderRadius: radius.input,
        backgroundColor: auth ? (focused ? colors.leitnerActiveBg : isDark ? colors.softBg : colors.appBg)
          : focused ? colors.leitnerActiveBg : nested ? colors.softBg : colors.inputBg,
        paddingHorizontal: 16,
        justifyContent: "center",
      }]}
    >
      <TextInput
        placeholderTextColor={colors.muted}
        accessibilityLabel={label}
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
          auth && {
            minHeight: 52, width: "100%", backgroundColor: "transparent", borderWidth: 0,
            ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as object) : {}),
          },
        ]}
      />
    </SquircleView>
  );
  return label ? <View style={{ gap: 5 }}><AppText size={13} weight="700">{label}</AppText>{field}</View> : field;
}
