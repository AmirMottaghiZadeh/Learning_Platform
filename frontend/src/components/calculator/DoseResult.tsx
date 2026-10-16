import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { parseMeasure, splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Extras, Ltr, ResultCard, ResultProps, Rows, useShown } from "./common";

/** A dose, volume or rate: the amount large with its unit, the inputs it was
 * worked out from (so a wrong entry is easy to spot), and a standing reminder
 * to check it against local protocol. */
export function DoseResult({ results, inputs }: ResultProps) {
  const { colors } = useTheme();
  const { t, isFa } = useLang();
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "numunit") ?? results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const m = parseMeasure(primary.answerText ?? "");
  const lead = splitLeadingNumber(primary.answerText ?? "");
  const rest = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text);

  return (
    <ResultCard title={p.title}>
      <View style={{ flexDirection: "row", alignItems: "baseline", gap: 8, direction: "ltr", flexWrap: "wrap" }}>
        <AppText weight="900" size={42} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 52 }}>
          {m ? m.main.value : lead ? lead.value : p.text}
        </AppText>
        {m?.main.unit ? (
          <Ltr size={16} muted>
            {m.main.unit}
          </Ltr>
        ) : null}
      </View>
      <Extras items={rest} />
      {inputs.length ? (
        <View style={{ gap: 2 }}>
          <AppText weight="800" size={12} muted style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
            {t("calcInputsUsed")}
          </AppText>
          <Rows rows={inputs} />
        </View>
      ) : null}
      <View
        style={{
          borderRadius: 10,
          borderWidth: 1,
          borderColor: colors.cautBorder,
          backgroundColor: colors.cautBg,
          paddingHorizontal: 10,
          paddingVertical: 7,
        }}
      >
        <AppText weight="700" size={11.5} color={colors.cautLabel} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
          {t("calcDoseWarning")}
        </AppText>
      </View>
    </ResultCard>
  );
}
