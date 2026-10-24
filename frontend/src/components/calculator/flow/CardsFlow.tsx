import React, { useEffect, useMemo, useRef } from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { choiceWeights } from "@/utils/calculatorLive";

import { LiveScore } from "./LiveScore";
import { QuestionField, isBinaryQuestion } from "./QuestionField";
import { FlowProps } from "./types";

const AUTO_NEXT_MS = 260;

/** One question per screen, large, under a bar with a segment per question.
 * A yes/no answer moves on by itself. With `live` the score so far, its tier
 * and the tier bar sit on top and each choice shows its weight. */
export function CardsFlow({ live, ...p }: FlowProps & { live: boolean }) {
  const { colors } = useTheme();
  const { t, n, isFa, row } = useLang();
  const { data, answers, step } = p;
  const question = data.questions[step];
  const total = data.questions.length;
  const last = step === total - 1;
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const weights = useMemo(() => (live ? choiceWeights(data, question, answers) : null), [live, data, question, answers]);
  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const binary = isBinaryQuestion(question, isFa);
  const onChoose = (index: number, value: number | undefined) => {
    p.setError(null);
    p.choose(question.position, index, value);
    if (binary && value !== undefined && !last) {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => p.setStep((s) => (s === step ? s + 1 : s)), AUTO_NEXT_MS);
    }
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
      />

      {binary && !last ? (
        <AppText muted weight="600" size={11.5} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
          {t("calcAutoNext")}
        </AppText>
      ) : null}

      {p.error ? (
        <AppText size={12} weight="700" color={colors.denyLabel}>
          {p.error}
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
          disabled={p.validate(question, answers[question.position]) !== null}
          style={{ flex: 1 }}
        />
      </View>
    </View>
  );
}
