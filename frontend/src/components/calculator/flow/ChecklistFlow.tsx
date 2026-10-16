import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

import { LiveScore } from "./LiveScore";
import { QuestionField } from "./QuestionField";
import { FlowProps } from "./types";

/** Every question on one page, each with its answer control beside or under
 * it, and a count of what is answered. The button turns on when all are. */
export function ChecklistFlow(p: FlowProps) {
  const { colors } = useTheme();
  const { t, n, isFa, row } = useLang();
  const { data, answers } = p;
  const answered = data.questions.filter((q) => answers[q.position] !== undefined && p.validate(q, answers[q.position]) === null).length;
  const total = data.questions.length;

  return (
    <View style={{ gap: spacing.md, marginBottom: spacing.lg }}>
      {p.info.model === "score" ? <LiveScore data={data} answers={answers} /> : null}

      <AppText muted weight="600" size={12} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
        {t("calcListHint")}
      </AppText>

      <Card padded={false} style={{ overflow: "hidden" }}>
        {data.questions.map((q, i) => (
          <View
            key={q.position}
            style={{ padding: spacing.md, borderTopWidth: i === 0 ? 0 : 1, borderTopColor: colors.border }}
          >
            <QuestionField
              question={q}
              variant="row"
              value={answers[q.position]}
              choiceIndex={p.choiceIndexes[q.position]}
              unitIndex={p.unitIndexes[q.position] ?? 0}
              onChange={(v) => {
                p.setError(null);
                p.setAnswer(q.position, v);
              }}
              onChoose={(index, v) => {
                p.setError(null);
                p.choose(q.position, index, v);
              }}
              onUnit={(index) => {
                p.setError(null);
                p.setUnit(q.position, index);
              }}
              showWeights={false}
            />
          </View>
        ))}
      </Card>

      {p.error ? (
        <AppText size={12} weight="700" color={colors.denyLabel}>
          {p.error}
        </AppText>
      ) : null}

      <Card style={{ gap: 10 }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: 10 }}>
          <AppText weight="800" size={13} style={{ flex: 1, writingDirection: isFa ? "rtl" : "ltr" }}>
            {n(answered)} {t("calcOutOf")} {n(total)} {t("calcAnsweredWord")}
          </AppText>
          <Button label={t("calculatorComputeBtn")} onPress={p.compute} disabled={answered < total} style={{ minWidth: 120 }} />
        </View>
        {answered < total ? (
          <AppText muted weight="600" size={11.5} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
            {t("calcFillAll")}
          </AppText>
        ) : null}
      </Card>
    </View>
  );
}
