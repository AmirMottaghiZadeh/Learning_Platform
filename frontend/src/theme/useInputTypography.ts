import { StyleSheet, TextInputProps, TextStyle } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { hasPersianLetters } from "@/utils/bidi";
import { FontWeight } from "./fonts";
import { useTypography } from "./TypographyProvider";

export function useInputTypography({ style, value, defaultValue, placeholder }: TextInputProps): TextStyle {
  const { isFa } = useLang();
  const { family } = useTypography();
  const base = StyleSheet.flatten(style);
  const text = value || defaultValue || placeholder || "";
  const script = hasPersianLetters(text) || (isFa && !/[A-Za-z]/.test(text)) ? "fa" : "en";
  const match = base?.fontFamily?.match(/^Vazirmatn_([4-9]00)/);
  return {
    fontFamily: !base?.fontFamily || match ? family(script, match?.[1] as FontWeight | undefined) : base.fontFamily,
    fontSize: base?.fontSize ?? 15,
    lineHeight: base?.lineHeight,
  };
}
