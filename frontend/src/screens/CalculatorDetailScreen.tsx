import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { calculatorsApi } from "@/api/endpoints";
import { CalculatorQuestion } from "@/api/types";
import { ResultsView } from "@/components/calculator/ResultsView";
import { DateInput, DaysInput } from "@/components/calculator/DateInput";
import { describeInputs } from "@/components/calculator/common";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import {
  CalculatorAnswers,
  ComputedResult,
  ResultRange,
  checkErrors,
  computeCalculator,
  computeResultRanges,
  hasUnsupportedQuestions,
  unitFactorOf,
} from "@/utils/calculatorEngine";
import { classifyCalculator, isDisplayedResult } from "@/utils/calculatorModel";
import { AboutBlock, parseAboutHtml, stripHtml } from "@/utils/html";

/** Right-aligned/RTL for the real Persian content now available, left/LTR
 * for the untranslated-fallback or English-mode case -- the same per-element
 * pick every other bilingual screen this session uses, inlined here since
 * each function below has its own `isFa` from its own useLang() call. */
function dirStyle(isFa: boolean) {
  return {
    textAlign: isFa ? ("right" as const) : ("left" as const),
    writingDirection: isFa ? ("rtl" as const) : ("ltr" as const),
  };
}

export function CalculatorDetailScreen() {
  const { t, n, isFa, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const slug = String(useNav((s) => s.params.slug ?? ""));

  const [answers, setAnswers] = useState<CalculatorAnswers>({});
  // Which choice was tapped, per question position. The formula only needs
  // the choice's value (`answers`), but several choices can share one value
  // (e.g. "Left" and "Right" both scoring 1), so highlighting by value alone
  // would light up every choice with that score.
  const [choiceIndexes, setChoiceIndexes] = useState<Record<number, number>>({});
  // Which of a numeric question's units the learner picked (default: the first).
  const [unitIndexes, setUnitIndexes] = useState<Record<number, number>>({});
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ComputedResult[] | null>(null);
  // Computed alongside `results`, not eagerly on load: sweeping every
  // possible answer combination is real work, worth doing once right after
  // the learner asks for a result, not on every screen open.
  const [ranges, setRanges] = useState<Map<number, ResultRange>>(new Map());
  // The same results in the other unit system, for formulas that have one.
  const [altResults, setAltResults] = useState<ComputedResult[] | null>(null);
  const [meaningOpen, setMeaningOpen] = useState(false);
  // Back from the result returns to editing the answers, and from a later
  // question to the previous one, before leaving the calculator.
  useBackInterceptor(results !== null || step > 0, () => {
    setError(null);
    if (results !== null) {
      setResults(null);
      setStep(0);
    } else {
      setStep((s) => Math.max(0, s - 1));
    }
  });

  const { data, isLoading } = useQuery({
    queryKey: ["calculator", slug],
    queryFn: () => calculatorsApi.detail(slug),
    enabled: !!slug,
  });

  if (isLoading || !data) return <LoadingState />;

  const unsupported = hasUnsupportedQuestions(data.questions);
  const modelInfo = classifyCalculator(data);
  const shownPositions = new Set(data.results.filter(isDisplayedResult).map((r) => r.position));

  const setAnswer = (position: number, value: number | undefined) => {
    setAnswers((cur) => {
      const next = { ...cur };
      if (value === undefined) delete next[position];
      else next[position] = value;
      return next;
    });
  };

  /** Null when `value` is acceptable; an error message otherwise -- shared
   * by per-step "Next" gating and the final defensive re-check in compute(). */
  const validate = (q: CalculatorQuestion, value: number | undefined): string | null => {
    if (value === undefined) return t("calculatorFillRequired");
    const unit = q.units[unitIndexes[q.position] ?? 0] ?? q.units[0];
    if (unit) {
      // `value` is already multiplied by unit_factor; the unit's limits are
      // in the unit the learner typed in.
      const typed = Number((value / unitFactorOf(unit)).toPrecision(12));
      const min = unit.min_value ? parseFloat(unit.min_value) : NaN;
      const max = unit.max_value ? parseFloat(unit.max_value) : NaN;
      if ((!Number.isNaN(min) && typed < min) || (!Number.isNaN(max) && typed > max)) {
        const minMsg = isFa ? unit.min_value_msg_fa || unit.min_value_msg : unit.min_value_msg;
        const maxMsg = isFa ? unit.max_value_msg_fa || unit.max_value_msg : unit.max_value_msg;
        return minMsg || maxMsg || t("calculatorOutOfRange");
      }
    }
    return null;
  };

  const compute = () => {
    for (const q of data.questions) {
      const err = validate(q, answers[q.position]);
      if (err) {
        setError(err);
        setResults(null);
        return;
      }
    }
    const failedCheck = checkErrors(data.questions, data.error_checks, answers);
    if (failedCheck) {
      const message = isFa && failedCheck.answer_fa ? failedCheck.answer_fa : failedCheck.answer;
      setError(message || t("calculatorOutOfRange"));
      setResults(null);
      return;
    }
    setError(null);
    setResults(computeCalculator(data.questions, data.results, answers, { stringsFa: data.formula_strings_fa }));
    setAltResults(
      data.results.some((r) => /user_units/.test(r.formula ?? ""))
        ? computeCalculator(data.questions, data.results, answers, { stringsFa: data.formula_strings_fa, unitSystem: "us" })
        : null,
    );
    // The result itself (above) is cheap -- shows immediately on tap. The
    // full achievable range (for the gauge) sweeps many answer combinations
    // and can take up to ~1s for a calculator with several numeric
    // questions; deferred one tick so that result renders first instead of
    // the tap appearing to hang while the range search runs.
    setRanges(new Map());
    setTimeout(
      () => setRanges(computeResultRanges(data.questions, data.results, answers, data.formula_strings_fa)),
      0,
    );
  };

  const isLastStep = step === data.questions.length - 1;
  const currentQuestion = data.questions[step];

  const goNext = () => {
    const err = validate(currentQuestion, answers[currentQuestion.position]);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    if (isLastStep) compute();
    else setStep((s) => s + 1);
  };

  const goPrev = () => {
    setError(null);
    setStep((s) => Math.max(0, s - 1));
  };

  const editAnswers = () => {
    setResults(null);
    setError(null);
    setStep(0);
  };

  return (
    <Screen>
      <ScreenChrome title={t("calculatorScreenTitle")} onBack={goBack} />

      <AppText weight="900" size={22} style={{ lineHeight: 30, marginBottom: 8, ...dirStyle(isFa) }}>
        {stripHtml(isFa && data.name_fa ? data.name_fa : data.name)}
      </AppText>

      {data.description || data.description_fa ? (
        <AppText muted weight="600" size={13} style={{ marginBottom: 16, lineHeight: 20, ...dirStyle(isFa) }}>
          {stripHtml(isFa && data.description_fa ? data.description_fa : data.description)}
        </AppText>
      ) : null}

      {unsupported ? (
        <Card style={{ marginBottom: spacing.lg }}>
          <AppText weight="700" size={13} color={colors.denyLabel}>
            {t("calculatorUnsupported")}
          </AppText>
        </Card>
      ) : results === null ? (
        <View style={{ marginBottom: spacing.lg }}>
          <AppText weight="800" size={12} muted style={{ marginBottom: spacing.lg, ...dirStyle(isFa) }}>
            {n(step + 1)} {t("calculatorStepOf")} {n(data.questions.length)}
          </AppText>

          {currentQuestion.type === "date_input" ? (
            <DateInput
              key={`${currentQuestion.position}-${isFa}`}
              question={currentQuestion}
              value={answers[currentQuestion.position]}
              onChange={(v) => setAnswer(currentQuestion.position, v)}
            />
          ) : currentQuestion.type === "days_input" ? (
            <DaysInput
              key={currentQuestion.position}
              question={currentQuestion}
              value={answers[currentQuestion.position]}
              onChange={(v) => setAnswer(currentQuestion.position, v)}
            />
          ) : (
            <QuestionInput
              key={currentQuestion.position}
              question={currentQuestion}
              value={answers[currentQuestion.position]}
              onChange={(v) => setAnswer(currentQuestion.position, v)}
              choiceIndex={choiceIndexes[currentQuestion.position]}
              unitIndex={unitIndexes[currentQuestion.position] ?? 0}
              onUnit={(index) => {
                setError(null);
                setUnitIndexes((cur) => ({ ...cur, [currentQuestion.position]: index }));
              }}
              onChoose={(index, v) => {
                setChoiceIndexes((cur) => ({ ...cur, [currentQuestion.position]: index }));
                setAnswer(currentQuestion.position, v);
              }}
            />
          )}

          {error ? (
            <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginTop: 14 }}>
              {error}
            </AppText>
          ) : null}

          <View style={{ flexDirection: row, gap: 10, marginTop: spacing.lg }}>
            {step > 0 ? (
              <Button label={t("calculatorPrevious")} variant="secondary" onPress={goPrev} style={{ flex: 1 }} />
            ) : null}
            <Button
              label={isLastStep ? t("calculatorComputeBtn") : t("calculatorNext")}
              onPress={goNext}
              disabled={validate(currentQuestion, answers[currentQuestion.position]) !== null}
              style={{ flex: 1 }}
            />
          </View>
        </View>
      ) : (
        <View style={{ gap: 10, marginBottom: spacing.lg }}>
          <ResultsView
            data={data}
            info={modelInfo}
            results={results.filter((r) => r.visible && r.answerText !== null && shownPositions.has(r.position))}
            ranges={ranges}
            answers={answers}
            altResults={altResults}
            inputs={describeInputs(data, answers, choiceIndexes, unitIndexes, isFa, stripHtml, unitFactorOf)}
          />

          {data.about || data.about_fa ? (
            <View style={{ borderRadius: 14, backgroundColor: colors.softBg, overflow: "hidden" }}>
              <Pressable
                onPress={() => setMeaningOpen((v) => !v)}
                style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", padding: 14 }}
              >
                <AppText weight="800" size={13}>
                  {t("calculatorScoreMeaningLabel")}
                </AppText>
                <AppText weight="700" size={11} color={colors.accent}>
                  {meaningOpen ? "▲" : "▼"}
                </AppText>
              </Pressable>
              {meaningOpen ? (
                <View style={{ paddingHorizontal: 14, paddingBottom: 14 }}>
                  <AboutBody html={isFa && data.about_fa ? data.about_fa : data.about} />
                </View>
              ) : null}
            </View>
          ) : null}

          <Pressable onPress={editAnswers} style={{ alignSelf: "flex-start", paddingVertical: 6 }}>
            <AppText weight="800" size={12.5} color={colors.accent}>
              {t("calculatorEditAnswers")}
            </AppText>
          </Pressable>

          {data.references.length ? (
            <View style={{ marginTop: 6 }}>
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
        </View>
      )}

      {data.disclaimer_footer || data.disclaimer_footer_fa ? (
        <AppText muted weight="600" size={11} style={{ lineHeight: 17, marginBottom: 14, ...dirStyle(isFa) }}>
          {stripHtml(
            isFa && data.disclaimer_footer_fa ? data.disclaimer_footer_fa : data.disclaimer_footer,
          )}
        </AppText>
      ) : null}
    </Screen>
  );
}

/** Renders the calculator's "about" HTML as real headings/paragraphs/list
 * items (see parseAboutHtml) instead of one flat run of lines -- the
 * criteria lists and "Score X: meaning" labels this content routinely has
 * were unreadable collapsed to plain text with no bullets or emphasis. */
function AboutBody({ html }: { html: string }) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const blocks: AboutBlock[] = parseAboutHtml(html);

  return (
    <View style={{ gap: 10 }}>
      {blocks.map((b, i) => {
        if (b.kind === "heading") {
          return (
            <AppText key={i} weight="800" size={13} style={dirStyle(isFa)}>
              {b.text}
            </AppText>
          );
        }
        const label = b.label ? (
          <AppText weight="800" size={13} color={colors.ink}>
            {b.label}:{" "}
          </AppText>
        ) : null;
        if (b.kind === "listItem") {
          return (
            <View key={i} style={{ flexDirection: row, gap: 8 }}>
              <AppText weight="700" size={13} color={colors.accent}>
                •
              </AppText>
              <AppText
                weight="500"
                size={13}
                style={{ flex: 1, lineHeight: 20, ...dirStyle(isFa) }}
              >
                {label}
                {b.text}
              </AppText>
            </View>
          );
        }
        return (
          <AppText key={i} weight="500" size={13} style={{ lineHeight: 21, ...dirStyle(isFa) }}>
            {label}
            {b.text}
          </AppText>
        );
      })}
    </View>
  );
}

function QuestionInput({
  question,
  value,
  onChange,
  choiceIndex,
  unitIndex,
  onUnit,
  onChoose,
}: {
  question: CalculatorQuestion;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  choiceIndex: number | undefined;
  unitIndex: number;
  onUnit: (index: number) => void;
  onChoose: (index: number, value: number | undefined) => void;
}) {
  const { colors, shadows } = useTheme();
  const { isFa, row } = useLang();
  const unit = question.units[unitIndex] ?? question.units[0];

  const unitFactor = () => unitFactorOf(unit);

  // The TextInput shows what the user typed, in their units; `value` (what
  // the parent tracks) is already multiplied by unit_factor for the formula
  // engine, so the two can legitimately differ and the input must not be
  // controlled from `value` directly. It's still the right *initial* text
  // though -- this question remounts fresh each time the stepper revisits
  // it (a new `key` per step), so without seeding from `value` here, going
  // back to an already-answered numeric question would show it as blank.
  const [text, setText] = useState(() => (value === undefined ? "" : String(Number((value / unitFactor()).toFixed(6)))));

  return (
    <View>
      <AppText weight="700" size={13.5} style={{ lineHeight: 20, ...dirStyle(isFa) }}>
        {stripHtml(isFa && question.title_fa ? question.title_fa : question.title)}
      </AppText>
      {question.more_information || question.more_information_fa ? (
        <AppText muted weight="600" size={12} style={{ marginTop: 3, lineHeight: 18, ...dirStyle(isFa) }}>
          {stripHtml(
            isFa && question.more_information_fa
              ? question.more_information_fa
              : question.more_information ?? "",
          )}
        </AppText>
      ) : null}

      {question.type === "multiple_choice" ? (
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8, marginTop: 10 }}>
          {question.choices.map((choice, i) => {
            const factor = choice.answer_factor !== null ? parseFloat(choice.answer_factor) : NaN;
            const selected = choiceIndex === i && value !== undefined;
            const choiceLabel = isFa && choice.title_primary_fa ? choice.title_primary_fa : choice.title_primary;
            return (
              <Pressable
                key={i}
                onPress={() => onChoose(i, Number.isNaN(factor) ? undefined : factor)}
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
                  {stripHtml(choiceLabel)}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      ) : (
        <View
          style={[
            {
              // The number, then its unit on the right, in both languages --
              // so not the language-dependent `row`.
              flexDirection: "row",
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
              const num = parseFloat(next);
              if (next.trim() === "" || Number.isNaN(num)) {
                onChange(undefined);
                return;
              }
              onChange(num * unitFactor());
            }}
            keyboardType="decimal-pad"
            selectTextOnFocus
            autoComplete="off"
            autoCorrect={false}
            textContentType="none"
            importantForAutofill="no"
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
            <AppText muted weight="700" size={12} style={{ textAlign: "left", writingDirection: "ltr" }}>
              {stripHtml(isFa && unit.title_fa ? unit.title_fa : unit.title)}
            </AppText>
          ) : null}
        </View>
      )}

      {question.type !== "multiple_choice" && question.units.length > 1 ? (
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8, marginTop: 10 }}>
          {question.units.map((u, i) => {
            const selected = i === unitIndex;
            return (
              <Pressable
                key={i}
                onPress={() => {
                  if (selected) return;
                  // Keep the quantity, change how it is written: 30 g/L
                  // becomes 3 g/dL rather than staying "30".
                  if (value !== undefined) setText(String(Number((value / unitFactorOf(u)).toFixed(6))));
                  onUnit(i);
                }}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 7,
                  borderRadius: 999,
                  borderWidth: 1,
                  borderColor: selected ? colors.accent : colors.trackBg,
                  backgroundColor: selected ? `${colors.accent}1a` : colors.softBg,
                }}
              >
                <AppText weight="700" size={12} color={selected ? colors.accent : colors.ink}>
                  {stripHtml(isFa && u.title_fa ? u.title_fa : u.title)}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}
