import React, { useMemo } from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { choiceWeights } from "@/utils/calculatorLive";

import { LiveScore } from "./LiveScore";
import { QuestionField } from "./QuestionField";
import { FlowProps } from "./types";

/** One question per screen, large, under a bar with a segment per question.
 * Only the Next button moves on, never a choice by itself. With `live` the
 * score so far, its tier and the tier bar sit on top and each choice shows
 * its weight. */
export function CardsFlow({ live, ...p }: FlowProps & { live: boolean }) {
  const { colors } = useTheme();
  const { t, n, isFa, row } = useLang();
  const { data, answers, step } = p;
  const question = data.questions[step];
  const total = data.questions.length;
  const last = step === total - 1;
  const weights = useMemo(() => (live ? choiceWeights(data, question, answers) : null), [live, data, question, answers]);
  const answer = answers[question.position];
  // An answer the button refuses (out of range) says why right away; the
  // button is off, so pressing it could not show the message.
  const problem = answer !== undefined ? p.validate(question, answer) : null;

  const onChoose = (index: number, value: number | undefined) => {
    p.setError(null);
    p.choose(question.position, index, value);
  };

  const next = () => {
    const err = p.validate(question, answers[question.position]);
    if (err) return p.setError(err);
    p.setError(null);
    if (last) p.compute();
    else p.setStep((s) => s + 1);
  };

  return (
    <View style={{ gap: spacing.md, marginBottom: spacing.lg }}>
      {live ? <LiveScore data={data} answers={answers} /> : null}

      <View style={{ flexDirection: row, gap: 4 }}>
        {data.questions.map((q, k) => {
          const done = k !== step && (k < step || answers[q.position] !== undefined);
          return (
            <View
              key={q.position}
              style={{
                flex: 1,
                height: 5,
                borderRadius: 3,
                backgroundColor: done ? colors.accent : k === step ? `${colors.accent}73` : colors.trackBg,
              }}
            />
          );
        })}
      </View>
      <AppText weight="800" size={12} muted style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
        {t("calcQuestion")} {n(step + 1)} {t("calcOutOf")} {n(total)}
      </AppText>

      <QuestionField
        key={question.position}
        question={question}
        variant="card"
        value={answers[question.position]}
        choiceIndex={p.choiceIndexes[question.position]}
        unitIndex={p.unitIndexes[question.position] ?? 0}
        onChange={(v) => p.setAnswer(question.position, v)}
        onChoose={onChoose}
        onUnit={(i) => {
          p.setError(null);
          p.setUnit(question.position, i);
        }}
        weights={weights}
        unitSystem={p.unitSystem}
      />

      {p.error || problem ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
          {p.error ?? problem}
        </AppText>
      ) : null}

      <View style={{ flexDirection: row, gap: 10, marginTop: spacing.sm }}>
        {step > 0 ? (
          <Button
            label={t("calculatorPrevious")}
            variant="secondary"
            onPress={() => {
              p.setError(null);
              p.setStep((s) => Math.max(0, s - 1));
            }}
            style={{ flex: 1 }}
          />
        ) : null}
        <Button
          label={last ? t("calculatorComputeBtn") : t("calculatorNext")}
          onPress={next}
          disabled={answer === undefined || problem !== null}
          style={{ flex: 1 }}
        />
      </View>
    </View>
  );
}
