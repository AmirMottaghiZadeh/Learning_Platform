import React from "react";
import { StyleProp, Text, TextProps, TextStyle } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { FontWeight, fontFamily } from "@/theme/fonts";

type Props = TextProps & {
  weight?: FontWeight;
  size?: number;
  color?: string;
  muted?: boolean;
  center?: boolean;
  style?: StyleProp<TextStyle>;
};

export function AppText({
  weight = "400",
  size = 15,
  color,
  muted,
  center,
  style,
  children,
  ...rest
}: Props) {
  const { colors } = useTheme();
  const { dir } = useLang();
  return (
    <Text
      {...rest}
      style={[
        {
          fontFamily: fontFamily(weight),
          fontSize: size,
          lineHeight: Math.round(size * 1.7),
          color: color ?? (muted ? colors.muted : colors.ink),
          writingDirection: dir,
          textAlign: center ? "center" : dir === "rtl" ? "right" : "left",
        },
        style,
      ]}
    >
      {children}
    </Text>
  );
}
