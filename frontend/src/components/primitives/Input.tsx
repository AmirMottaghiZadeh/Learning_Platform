import React, { useContext, useState } from "react";
import { TextInputProps } from "react-native";
import { TextInput } from "@/components/primitives/TextInput";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { radius } from "@/theme/tokens";
import { useTypography } from "@/theme/TypographyProvider";
import { SquircleView } from "./SquircleView";
import { CardSurface } from "./Card";

type Props = TextInputProps;

export function Input(props: Props) {
  const { colors, shadows } = useTheme();
  const nested = useContext(CardSurface);
  const { dir } = useLang();
  const { scale } = useTypography();
  const [focused, setFocused] = useState(false);
  return (
    <SquircleView
      style={[!nested && shadows.surface, {
        minHeight: Math.max(48, Math.ceil(32 * scale + 12)),
        borderRadius: radius.input,
        backgroundColor: focused ? colors.leitnerActiveBg : nested ? colors.softBg : colors.inputBg,
        paddingHorizontal: 16,
        justifyContent: "center",
      }]}
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
    </SquircleView>
  );
}
