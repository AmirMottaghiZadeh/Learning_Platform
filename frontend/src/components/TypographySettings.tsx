import React, { useRef, useState } from "react";
import { Pressable, View } from "react-native";

import { AppText, ReadingTextScope } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { READING_SIZE_OPTIONS, useReader, useReaderScale } from "@/store/reader";
import { squircle } from "@/theme/squircle";
import { useTheme } from "@/theme/ThemeProvider";
import { FONT_OPTIONS, useTypography } from "@/theme/TypographyProvider";
import { radius, spacing } from "@/theme/tokens";

type Choice = {
  label: string;
  selected: boolean;
  disabled?: boolean;
  onPress: () => void;
};

function FontChoice({ label, selected, disabled, onPress }: Choice) {
  const { colors } = useTheme();
  return (
    <Pressable
      accessibilityRole="radio"
      aria-checked={selected}
      accessibilityState={{ checked: selected, disabled }}
      accessibilityLabel={label}
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
  const { fonts, setFont } = useTypography();
  const scale = useReaderScale();
  const setTextScale = useReader((state) => state.setTextScale);
  const readingSizeLabel = isFa ? "اندازهٔ متن مطالعه" : "Reading text size";
  const readingSizes = READING_SIZE_OPTIONS.some((size) => size === scale)
    ? READING_SIZE_OPTIONS
    : [...READING_SIZE_OPTIONS, scale].sort((a, b) => a - b);
  const inProgress = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const choose = async (apply: () => Promise<void>) => {
    if (inProgress.current) return;
    inProgress.current = true;
    setPending(true);
    setError("");
    try {
      await apply();
    } catch {
      setError(isFa ? "ذخیرهٔ تنظیمات فونت ممکن نشد. دوباره تلاش کنید." : "Could not save typography settings. Try again.");
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
              {FONT_OPTIONS[script].map(({ id, label: name }) => (
                <FontChoice key={id} label={name} selected={fonts[script] === id} disabled={pending}
                  onPress={() => void choose(() => setFont(script, id))} />
              ))}
            </View>
          </View>
        );
      })}
      <View style={{ gap: spacing.sm }}>
        <AppText weight="700" size={14}>{readingSizeLabel}</AppText>
        <View accessibilityRole="radiogroup" accessibilityLabel={readingSizeLabel} style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
          {readingSizes.map((value) => (
            <FontChoice key={value} label={isFa ? `${n(Math.round(value * 100))}٪` : `${Math.round(value * 100)}%`}
              selected={scale === value} disabled={pending} onPress={() => void choose(async () => setTextScale(value))} />
          ))}
        </View>
      </View>
      <Card soft style={{ gap: spacing.xs }}>
        <ReadingTextScope>
          <AppText weight="700">{isFa ? "دارونامه و منابع بالینی" : "Clinical references and drug information"}</AppText>
          <AppText size={13} muted style={{ writingDirection: isFa ? "ltr" : "rtl" }}>{isFa ? "Read about medicines and clinical topics." : "مطالعهٔ داروها و موضوعات بالینی"}</AppText>
        </ReadingTextScope>
      </Card>
      {error ? <AppText accessibilityRole="alert" size={13}>{error}</AppText> : null}
    </Card>
  );
}
