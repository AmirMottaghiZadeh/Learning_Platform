import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { calculatorsApi } from "@/api/endpoints";
import { CalculatorQuestion } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import {
  CalculatorAnswers,
  ComputedResult,
  computeCalculator,
  hasUnsupportedQuestions,
} from "@/utils/calculatorEngine";
import { htmlToParagraphs, stripHtml } from "@/utils/html";

export function CalculatorDetailScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const slug = String(useNav((s) => s.params.slug ?? ""));

  const [answers, setAnswers] = useState<CalculatorAnswers>({});
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ComputedResult[] | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["calculator", slug],
    queryFn: () => calculatorsApi.detail(slug),
    enabled: !!slug,
  });

  if (isLoading || !data) return <LoadingState />;

  const unsupported = hasUnsupportedQuestions(data.questions);

  const setAnswer = (position: number, value: number | undefined) => {
    setResults(null);
    setError(null);
    setAnswers((cur) => {
      const next = { ...cur };
      if (value === undefined) delete next[position];
      else next[position] = value;
      return next;
    });
  };

  const compute = () => {
    for (const q of data.questions) {
      const value = answers[q.position];
      if (value === undefined) {
        setError(t("calculatorFillRequired"));
        setResults(null);
        return;
      }
      const unit = q.units[0];
      if (unit) {
        const min = unit.min_value !== null ? parseFloat(unit.min_value) : null;
        const max = unit.max_value !== null ? parseFloat(unit.max_value) : null;
        if ((min !== null && value < min) || (max !== null && value > max)) {
          setError(unit.min_value_msg || unit.max_value_msg || t("calculatorOutOfRange"));
          setResults(null);
          return;
        }
      }
    }
    setError(null);
    setResults(computeCalculator(data.questions, data.results, answers));
  };

  return (
    <Screen>
      <ScreenChrome title={t("calculatorScreenTitle")} onBack={goBack} />

      <AppText weight="900" size={22} style={{ lineHeight: 30, marginBottom: 8, textAlign: "left", writingDirection: "ltr" }}>
        {stripHtml(data.name)}
      </AppText>

      {data.description ? (
        <AppText muted weight="600" size={13} style={{ marginBottom: 16, lineHeight: 20 }}>
          {stripHtml(data.description)}
        </AppText>
      ) : null}

      {unsupported ? (
        <Card style={{ marginBottom: spacing.lg }}>
          <AppText weight="700" size={13} color={colors.denyLabel}>
            {t("calculatorUnsupported")}
          </AppText>
        </Card>
      ) : (
        <View style={{ gap: 14, marginBottom: spacing.lg }}>
          {data.questions.map((q) => (
            <QuestionInput
              key={q.position}
              question={q}
              value={answers[q.position]}
              onChange={(v) => setAnswer(q.position, v)}
            />
          ))}

          {error ? (
            <AppText size={12} weight="700" color={colors.denyLabel}>
              {error}
            </AppText>
          ) : null}

          <Pressable
            onPress={compute}
            style={{
              backgroundColor: colors.accent,
              borderRadius: 14,
              paddingVertical: 14,
              alignItems: "center",
            }}
          >
            <AppText weight="800" size={14} color={colors.onAccent}>
              {t("calculatorComputeBtn")}
            </AppText>
          </Pressable>
        </View>
      )}

      {results ? (
        <View style={{ gap: 10, marginBottom: spacing.lg }}>
          {results
            .filter((r) => r.visible && r.answerText !== null)
            .map((r) => (
              <Card key={r.position} style={{ gap: 4 }}>
                <AppText weight="800" size={13} style={{ textAlign: "left", writingDirection: "ltr" }}>
                  {stripHtml(r.title)}
                </AppText>
                <AppText
                  weight="900"
                  size={18}
                  color={colors.accent}
                  style={{ textAlign: "left", writingDirection: "ltr" }}
                >
                  {stripHtml(r.answerText ?? "")}
                </AppText>
              </Card>
            ))}
        </View>
      ) : null}

      {data.about ? (
        <View style={{ marginBottom: spacing.lg }}>
          <AppText weight="800" size={13} style={{ marginBottom: 6 }}>
            {t("calculatorAboutLabel")}
          </AppText>
          <AppText
            weight="600"
            size={13}
            style={{ lineHeight: 21, textAlign: "left", writingDirection: "ltr" }}
          >
            {htmlToParagraphs(data.about)}
          </AppText>
        </View>
      ) : null}

      {data.references.length ? (
        <View>
          <AppText weight="800" size={13} style={{ marginBottom: 6 }}>
            {t("calculatorReferencesLabel")}
          </AppText>
          <View style={{ gap: 6 }}>
            {data.references.map((ref, i) => (
              <AppText
                key={i}
                muted
                weight="600"
                size={11.5}
                style={{ lineHeight: 18, textAlign: "left", writingDirection: "ltr" }}
              >
                {[ref.names, stripHtml(ref.papers || ""), ref.sources].filter(Boolean).join(" — ")}
              </AppText>
            ))}
          </View>
        </View>
      ) : null}
    </Screen>
  );
}

function QuestionInput({
  question,
  value,
  onChange,
}: {
  question: CalculatorQuestion;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
}) {
  const { colors, shadows } = useTheme();
  const { row } = useLang();
  const unit = question.units[0];
  // The TextInput shows what the user typed, in their units; `value` (what
  // the parent tracks) is already multiplied by unit_factor for the formula
  // engine, so the two can legitimately differ and the input must not be
  // controlled from `value` directly.
  const [text, setText] = useState("");

  return (
    <View>
      <AppText weight="700" size={13.5} style={{ lineHeight: 20, textAlign: "left", writingDirection: "ltr" }}>
        {stripHtml(question.title)}
      </AppText>
      {question.more_information ? (
        <AppText muted weight="600" size={12} style={{ marginTop: 3, lineHeight: 18, textAlign: "left", writingDirection: "ltr" }}>
          {stripHtml(question.more_information)}
        </AppText>
      ) : null}

      {question.type === "multiple_choice" ? (
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8, marginTop: 10 }}>
          {question.choices.map((choice, i) => {
            const factor = choice.answer_factor !== null ? parseFloat(choice.answer_factor) : NaN;
            const selected = !Number.isNaN(factor) && value === factor;
            return (
              <Pressable
                key={i}
                onPress={() => onChange(Number.isNaN(factor) ? undefined : factor)}
                style={[
                  {
                    paddingHorizontal: 14,
                    paddingVertical: 9,
                    borderRadius: 999,
                    borderWidth: 1,
                    borderColor: selected ? colors.accent : colors.trackBg,
                    backgroundColor: selected ? `${colors.accent}1a` : colors.softBg,
                  },
                ]}
              >
                <AppText weight="700" size={12.5} color={selected ? colors.accent : colors.ink}>
                  {stripHtml(choice.title_primary)}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      ) : (
        <View
          style={[
            {
              flexDirection: row,
              alignItems: "center",
              gap: 8,
              marginTop: 10,
              backgroundColor: colors.inputBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              borderRadius: 12,
              paddingHorizontal: 12,
              paddingVertical: 10,
            },
            shadows.raisedSm,
          ]}
        >
          <TextInput
            value={text}
            onChangeText={(next) => {
              setText(next);
              const n = parseFloat(next);
              if (next.trim() === "" || Number.isNaN(n)) {
                onChange(undefined);
                return;
              }
              const factor = unit?.unit_factor !== null && unit?.unit_factor !== undefined
                ? parseFloat(unit.unit_factor)
                : 1;
              onChange(n * (Number.isNaN(factor) ? 1 : factor));
            }}
            keyboardType="numeric"
            placeholder="0"
            placeholderTextColor={colors.muted}
            style={{
              flex: 1,
              fontFamily: fontFamily("600"),
              fontSize: 14,
              color: colors.ink,
              textAlign: "left",
              writingDirection: "ltr",
              padding: 0,
            }}
          />
          {unit ? (
            <AppText muted weight="700" size={12}>
              {stripHtml(unit.title)}
            </AppText>
          ) : null}
        </View>
      )}
    </View>
  );
}
