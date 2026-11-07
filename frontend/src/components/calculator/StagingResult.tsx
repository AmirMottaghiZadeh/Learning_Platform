import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { resultText, tnmAxis, tnmTokens } from "@/utils/calculatorModel";

import { Extras, ResultCard, ResultProps, useShown } from "./common";

/** TNM staging as a table: one row each for the tumour, nodes and
 * metastasis codes with what the letter stands for, then the stage group
 * and anything else the calculator reports. */
export function StagingResult({ results, data }: ResultProps) {
  const { colors } = useTheme();
  const { t, row, isFa } = useLang();
  const shown = useShown();
  const axes: { key: "T" | "N" | "M"; label: string; hint: string }[] = [
    { key: "T", label: t("calcTumor"), hint: t("calcTumorHint") },
    { key: "N", label: t("calcNodes"), hint: t("calcNodesHint") },
    { key: "M", label: t("calcMetastasis"), hint: t("calcMetastasisHint") },
  ];
  const codes = new Map<string, string>();
  const rest: ReturnType<typeof shown>[] = [];
  for (const r of results) {
    const tokens = tnmTokens(r.answerText ?? "");
    const axis = tnmAxis(r.answerText ?? "");
    if (tokens) tokens.forEach((tk) => codes.set(tk.axis, tk.code));
    else if (axis && !codes.has(axis)) codes.set(axis, resultText(r.answerText));
    else rest.push(shown(r));
  }

  return (
    <ResultCard title={isFa ? data.name_fa || data.name : data.name}>
      <View>
        {axes
          .filter((a) => codes.has(a.key))
          .map((a, i) => (
            <View
              key={a.key}
              style={{
                flexDirection: row,
                alignItems: "center",
                justifyContent: "space-between",
                gap: 10,
                paddingVertical: 9,
                borderTopWidth: i === 0 ? 0 : 1,
                borderTopColor: colors.border,
              }}
            >
              <View style={{ flex: 1, gap: 1 }}>
                <AppText weight="800" size={13}>
                  {a.label}
                </AppText>
                <AppText weight="600" size={11.5} muted>
                  {a.hint}
                </AppText>
              </View>
              <View style={{ paddingHorizontal: 14, paddingVertical: 4, borderRadius: 999, backgroundColor: colors.specBg, borderWidth: 1, borderColor: colors.specBorder }}>
                <AppText weight="900" size={17} color={colors.specLabel} style={{ writingDirection: "ltr", textAlign: "left" }}>
                  {codes.get(a.key)}
                </AppText>
              </View>
            </View>
          ))}
      </View>
      <Extras items={rest.map((r) => ({ ...r, title: r.title || t("calcStageGroup") }))} />
    </ResultCard>
  );
}
