import React, { useState } from "react";
import { Pressable, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { formatDoseRange } from "@/pediatricDose/model";
import type { DoseResult, ProductResult, RegimenResult, Source } from "@/pediatricDose/types";

export function PediatricNotice({ children, error = false }: { children: React.ReactNode; error?: boolean }) {
  const { colors } = useTheme();
  return <View style={{ backgroundColor: error ? colors.denyBg : colors.cautBg, borderRadius: 12, padding: 12 }}>
    <AppText accessibilityRole={error ? "alert" : undefined} size={13} color={error ? colors.denyLabel : colors.cautInk}>{children}</AppText>
  </View>;
}

export function PediatricSource({ regimen, onOpen }: { regimen: RegimenResult; onOpen: (source: Source) => void }) {
  const [open, setOpen] = useState(false);
  const { colors } = useTheme();
  const { isFa } = useLang();
  return <Card raised={false} style={{ gap: 12 }}>
    <Pressable accessibilityRole="button" accessibilityState={{ expanded: open }} onPress={() => setOpen(value => !value)} style={{ minHeight: 40, justifyContent: "center" }}>
      <AppText weight="800" size={13} color={colors.accent}>{isFa ? "منبع و متن پشتوانه · UpToDate" : "Source and supporting text · UpToDate"} {open ? "−" : "+"}</AppText>
    </Pressable>
    {open && <>
      <AppText size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{regimen.source.title}</AppText>
      {regimen.quotes.map((quote, index) => <View key={index} style={{ backgroundColor: colors.softBg, borderRadius: 10, padding: 12 }}>
        <AppText size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{quote}</AppText>
      </View>)}
      <Button label={isFa ? "خواندن منبع در آپتودیت" : "Read source in UpToDate"} variant="secondary" onPress={() => onOpen(regimen.source)} />
    </>}
  </Card>;
}

function unmeasurableText(product: ProductResult, isFa: boolean) {
  if (isFa) return product.amountText;
  if (product.reason === "unverified") return "The preparation's composition or strength is unverified; no volume is provided.";
  if (product.reason === "unmeasurable") return "This dose cannot be measured with this preparation's increments. A suitable measuring device or verified preparation/dilution is required.";
  return "The required amount cannot be delivered in whole or permitted half units with this preparation.";
}

export function PediatricDoseResult({ result, product, label }: { result: DoseResult; product: ProductResult; label?: string }) {
  const { colors } = useTheme();
  const { isFa, n } = useLang();
  const text = (fa: string, en: string) => isFa ? fa : en;
  const frequency = isFa ? result.freqFa : result.freqEn;
  return <View style={{ gap: 12 }}>
    {label && <AppText weight="800" size={15}>{label}</AppText>}
    <Card raised={false} style={{ padding: 20, gap: 12 }}>
      <AppText muted size={13}>{text("مقدار هر نوبت · فرآوردهٔ انتخابی", "Per administration · selected preparation")}</AppText>
      {product.ok && product.amount ? <>
        <AppText weight="800" size={38} color={colors.accent} style={{ writingDirection: "ltr", textAlign: "left" }}>
          {formatDoseRange(product.amount, isFa)} <AppText size={18} color={colors.accent}>{product.unit}</AppText>
        </AppText>
        <AppText weight="800" size={14}>{frequency}</AppText>
        {product.mg && !product.mgOnly && product.unit !== result.unit && <AppText muted size={13}>
          {text("معادل", "Equivalent to")} {formatDoseRange(product.mg, isFa)} {result.unit || "mg"}
        </AppText>}
      </> : <>
        <PediatricNotice>{unmeasurableText(product, isFa)}</PediatricNotice>
        {result.mgPerDose && <AppText weight="700" size={14}>
          {text("دوز محاسباتی دارو", "Calculated drug amount")}: {formatDoseRange(result.mgPerDose, isFa)} {result.unit}
        </AppText>}
        <AppText weight="700" size={13}>{frequency}</AppText>
      </>}
      <View style={{ borderTopWidth: 1, borderTopColor: colors.trackBg, paddingTop: 10 }}>
        <AppText size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{product.product}</AppText>
      </View>
    </Card>
    <Card raised={false} style={{ gap: 10 }}>
      {result.mgPerDay && <Metric label={text(result.schedule ? "مجموع در روز مصرف" : "مجموع روزانه", "Total per treatment day")} value={`${formatDoseRange(result.mgPerDay, isFa)} ${result.unit}`} />}
      {result.dailyMax != null && <Metric label={text("سقف روزانه", "Daily maximum")} value={`${n(result.dailyMax)} ${result.unit}`} />}
      {product.dailyMaxText && <Metric label={text("سقف روزانهٔ فرآورده", "Preparation daily maximum")} value={product.dailyMaxText} />}
      {product.components?.map(component => <Metric key={component.name} label={component.name} value={`${formatDoseRange(component.mgAtVolume, isFa)} mg`} />)}
      {result.capped.length > 0 && <PediatricNotice>{text("سقف دوز در محاسبه اعمال شده است.", "A maximum dose cap was applied.")}</PediatricNotice>}
      {result.schedule && <PediatricNotice>{isFa ? result.schedule.fa : result.schedule.en}</PediatricNotice>}
      {result.maxDosesPerDay != null && <PediatricNotice>{text("حداکثر تعداد نوبت در ۲۴ ساعت", "Maximum administrations in 24 hours")}: {n(result.maxDosesPerDay)}</PediatricNotice>}
      {result.maxDosesAtHigh != null && result.maxDosesAtHigh !== result.maxDosesPerDay && <PediatricNotice>{text("با دوز بالای بازه، حداکثر نوبت در ۲۴ ساعت", "At the upper dose, maximum administrations in 24 hours")}: {n(result.maxDosesAtHigh)}</PediatricNotice>}
      <AppText muted size={13}>{text("قاعدهٔ منبع", "Source rule")}</AppText>
      <AppText size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{result.order}</AppText>
    </Card>
  </View>;
}

export function Metric({ label, value }: { label: string; value: string }) {
  const { colors } = useTheme();
  const { row } = useLang();
  return <View style={{ flexDirection: row, alignItems: "flex-start", justifyContent: "space-between", gap: 14, paddingVertical: 7, borderBottomWidth: 1, borderBottomColor: colors.border }}>
    <AppText muted size={13} style={{ flex: 1 }}>{label}</AppText>
    <AppText weight="700" size={13} style={{ maxWidth: "62%", writingDirection: "ltr", textAlign: "left" }}>{value}</AppText>
  </View>;
}
