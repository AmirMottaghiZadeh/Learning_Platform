import React, { useRef, useState } from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { squircle } from "@/theme/squircle";
import { useTheme } from "@/theme/ThemeProvider";
import { FONT_OPTIONS, FONT_SCALES, useTypography } from "@/theme/TypographyProvider";
import { radius, spacing } from "@/theme/tokens";

type Choice = {
  label: string;
  selected: boolean;
  disabled?: boolean;
  onPress: () => void;
  description?: string;
};

function FontChoice({ label, selected, disabled, onPress, description }: Choice) {
  const { colors } = useTheme();
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: selected, disabled }}
      accessibilityLabel={description ? `${label}، ${description}` : label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => ({
        ...squircle,
        borderRadius: radius.sm,
        minHeight: 44,
        justifyContent: "center",
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.xs,
        backgroundColor: selected ? colors.accent : colors.softBg,
        opacity: pressed ? 0.8 : 1,
      })}
    >
      <AppText weight={selected ? "800" : "600"} size={13} color={selected ? colors.onAccent : colors.ink}>{label}</AppText>
    </Pressable>
  );
}

export function TypographySettings() {
  const { isFa, n, row } = useLang();
  const { fonts, scale, needsFile, setFont, setScale } = useTypography();
  const inProgress = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const choose = async (apply: () => Promise<void>, importFile = false) => {
    if (inProgress.current) return;
    inProgress.current = true;
    setPending(true);
    setError("");
    try {
      await apply();
    } catch {
      setError(importFile
        ? isFa ? "فونت بارگذاری نشد. یک فایل TTF یا OTF کوچک‌تر از ۱ مگابایت انتخاب کنید." : "The font could not be loaded. Choose a TTF or OTF file under 1 MB."
        : isFa ? "ذخیرهٔ تنظیمات فونت ممکن نشد. دوباره تلاش کنید." : "Could not save typography settings. Try again.");
    } finally {
      inProgress.current = false;
      setPending(false);
    }
  };

  return (
    <Card raised style={{ gap: spacing.md }}>
      <AppText accessibilityRole="header" weight="800" size={16}>{isFa ? "فونت و اندازهٔ متن" : "Font and text size"}</AppText>
      {(["fa", "en"] as const).map((script) => {
        const label = script === "fa" ? isFa ? "فونت فارسی" : "Persian font" : isFa ? "فونت انگلیسی" : "English font";
        return (
          <View key={script} style={{ gap: spacing.sm }}>
            <AppText weight="700" size={14}>{label}</AppText>
            <View accessibilityRole="radiogroup" accessibilityLabel={label} style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
              {FONT_OPTIONS[script].map(({ id, label: name }) => {
                const importFile = needsFile(id);
                return (
                  <FontChoice key={id} label={name} selected={fonts[script] === id} disabled={pending}
                    description={importFile ? isFa ? "انتخاب فایل فونت" : "Choose a font file" : undefined}
                    onPress={() => void choose(() => setFont(script, id), importFile)} />
                );
              })}
            </View>
          </View>
        );
      })}
      <AppText size={12} muted>
        {isFa ? "برای فونت‌هایی که روی دستگاه در دسترس نیستند، فایل TTF یا OTF را انتخاب کنید." : "Choose a TTF or OTF file for a font that is unavailable on your device."}
      </AppText>
      <View style={{ gap: spacing.sm }}>
        <AppText weight="700" size={14}>{isFa ? "اندازهٔ متن" : "Text size"}</AppText>
        <View accessibilityRole="radiogroup" accessibilityLabel={isFa ? "اندازهٔ متن" : "Text size"} style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
          {FONT_SCALES.map((value) => (
            <FontChoice key={value} label={isFa ? `${n(Math.round(value * 100))}٪` : `${Math.round(value * 100)}%`}
              selected={scale === value} disabled={pending} onPress={() => void choose(() => setScale(value))} />
          ))}
        </View>
      </View>
      <Card soft style={{ gap: spacing.xs }}>
        <AppText weight="700">{isFa ? "جست‌وجوی دارو و مرجع" : "Find drugs and references"}</AppText>
        <AppText size={13} muted style={{ writingDirection: isFa ? "ltr" : "rtl" }}>{isFa ? "Clinical references and drug information" : "دارونامه و منابع بالینی"}</AppText>
      </Card>
      {error ? <AppText accessibilityRole="alert" size={13}>{error}</AppText> : null}
    </Card>
  );
}
