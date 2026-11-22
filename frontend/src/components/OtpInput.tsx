import React, { useState } from "react";
import { Platform, StyleSheet, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { TextInput } from "@/components/primitives/TextInput";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

export function otpDigits(value: string, length: number) {
  return value
    .replace(/[۰-۹]/g, (digit) => String(digit.charCodeAt(0) - 0x06f0))
    .replace(/[٠-٩]/g, (digit) => String(digit.charCodeAt(0) - 0x0660))
    .replace(/\D/g, "")
    .slice(0, length);
}

type Props = {
  value: string;
  length: number;
  onChangeText: (value: string) => void;
  onSubmitEditing?: () => void;
  hasError?: boolean;
  sms?: boolean;
};

export function OtpInput({ value, length, onChangeText, onSubmitEditing, hasError, sms = false }: Props) {
  const { colors } = useTheme();
  const { n, t } = useLang();
  const [focused, setFocused] = useState(false);
  const activeCell = Math.min(value.length, length - 1);
  const label = t("otpPlaceholder");

  return (
    <View style={{ gap: 8 }}>
      <AppText size={14} weight="600">{label}</AppText>
      <View>
        <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden
          style={{ flexDirection: "row", gap: length > 6 ? 4 : 8, direction: "ltr" }}>
          {Array.from({ length }, (_, index) => {
            const selected = focused && index === activeCell;
            return (
              <View key={index} style={{ flex: 1, minHeight: 48, borderRadius: 10,
                alignItems: "center", justifyContent: "center",
                backgroundColor: hasError ? colors.denyBg : selected ? colors.trackBg : colors.softBg,
                }}>
                <AppText size={21} weight="600" style={{ writingDirection: "ltr", fontVariant: ["tabular-nums"] }}>
                  {value[index] ? n(value[index]) : ""}
                </AppText>
              </View>
            );
          })}
        </View>
        <TextInput
          testID="otp-input"
          accessibilityLabel={label}
          aria-invalid={hasError || undefined}
          aria-describedby={hasError ? "otp-error" : undefined}
          keyboardType="number-pad"
          inputMode="numeric"
          autoComplete={sms && Platform.OS === "android" ? "sms-otp" : "one-time-code"}
          textContentType="oneTimeCode"
          importantForAutofill="yes"
          autoFocus
          caretHidden
          selectionColor="transparent"
          value={value}
          onChangeText={(text) => onChangeText(otpDigits(text, length))}
          onSubmitEditing={onSubmitEditing}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={[StyleSheet.absoluteFill, {
            width: "100%", color: "transparent", backgroundColor: "transparent",
            padding: 0, fontFamily: fontFamily("500"), fontSize: 16, writingDirection: "ltr", textAlign: "left",
          }]}
        />
      </View>
    </View>
  );
}
