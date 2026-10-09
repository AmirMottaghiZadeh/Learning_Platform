import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";
import Svg, { Circle, Line, Path, Text as SvgText } from "react-native-svg";

import { calculatorsApi } from "@/api/endpoints";
import { CalculatorQuestion } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";
import {
  CalculatorAnswers,
  ComputedResult,
  ResultRange,
  checkErrors,
  classifyResultTone,
  computeCalculator,
  computeResultRanges,
  extractNumericValue,
  formatNumber,
  hasUnsupportedQuestions,
} from "@/utils/calculatorEngine";
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
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ComputedResult[] | null>(null);
  // Computed alongside `results`, not eagerly on load: sweeping every
  // possible answer combination is real work, worth doing once right after
  // the learner asks for a result, not on every screen open.
  const [ranges, setRanges] = useState<Map<number, ResultRange>>(new Map());
  const [meaningOpen, setMeaningOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["calculator", slug],
    queryFn: () => calculatorsApi.detail(slug),
    enabled: !!slug,
  });

  if (isLoading || !data) return <LoadingState />;

  const unsupported = hasUnsupportedQuestions(data.questions);

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
    const unit = q.units[0];
    if (unit) {
      const min = unit.min_value !== null ? parseFloat(unit.min_value) : null;
      const max = unit.max_value !== null ? parseFloat(unit.max_value) : null;
      if ((min !== null && value < min) || (max !== null && value > max)) {
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

          <QuestionInput
            key={currentQuestion.position}
            question={currentQuestion}
            value={answers[currentQuestion.position]}
            onChange={(v) => setAnswer(currentQuestion.position, v)}
            choiceIndex={choiceIndexes[currentQuestion.position]}
            onChoose={(index, v) => {
              setChoiceIndexes((cur) => ({ ...cur, [currentQuestion.position]: index }));
              setAnswer(currentQuestion.position, v);
            }}
          />

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
          {results
            .filter((r) => r.visible && r.answerText !== null)
            .map((r) => {
              // Always classified/measured from the English text -- see
              // calculatorEngine.ts's ComputedResult on why.
              const tone = classifyResultTone(r.answerText!);
              const tc = tone ? toneColors(tone, colors) : null;
              const range = ranges.get(r.position);
              const numericValue = extractNumericValue(r.answerText!);
              const displayTitle = isFa ? r.titleFa : r.title;
              const displayAnswer = isFa ? r.answerTextFa ?? r.answerText : r.answerText;
              return (
                <Card
                  key={r.position}
                  style={{
                    gap: 4,
                    ...(tc ? { backgroundColor: tc.bg, borderColor: tc.border } : null),
                  }}
                >
                  <AppText weight="800" size={13} style={dirStyle(isFa)}>
                    {stripHtml(displayTitle)}
                  </AppText>
                  <AppText
                    weight="900"
                    size={18}
                    color={tc ? tc.label : colors.accent}
                    style={{ textAlign: "center" }}
                  >
                    {stripHtml(displayAnswer ?? "")}
                  </AppText>
                  {range && numericValue !== null ? (
                    <ScoreGauge
                      value={numericValue}
                      range={range}
                      needleColor={tc ? tc.label : colors.accent}
                    />
                  ) : null}
                </Card>
              );
            })}

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

/** A half-circle dial, needle pointing from `range.min` (left) to
 * `range.max` (right) at this result's actual computed value -- `range` is
 * the calculator's own real achievable bounds (apps.calculators data swept
 * through every answer combination it allows, see computeResultRanges).
 * When the calculator's own data has more than one meaning across that
 * range (e.g. ASDAS-CRP legitimately crosses "Inactive" / "Moderate" /
 * "High" / "Very High" disease activity between its min and max), the arc
 * is drawn as one colored segment per band instead of a single flat track
 * -- a single min/max caption pair was hiding every band in between.
 * Colors reuse the same tone language as everywhere else in the app
 * (classifyResultTone -> toneColors), not invented ones. A calculator with
 * no dependent row at all (`range.bands` empty) falls back to one neutral
 * arc, same as before bands existed.
 *
 * "Glass/floating" styling, chosen from five mockups: a thinner,
 * rounded-cap arc instead of a flat band. (That style's floating value
 * badge over the dial was tried and dropped -- the card already shows
 * the answer prominently above the gauge, so repeating it inside the
 * dial was redundant clutter.) */
function ScoreGauge({
  value,
  range,
  needleColor,
}: {
  value: number;
  range: ResultRange;
  needleColor: string;
}) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const W = 260;
  const H = 150;
  const cx = W / 2;
  const cy = 115;
  const r = 92;
  const needleLen = 76;
  const strokeWidth = 10;

  // The dial itself stays min-left/max-right regardless of language -- a
  // gauge reads as a universal left-to-right scale even in an RTL app.
  const toFraction = (v: number) =>
    range.max > range.min ? Math.min(1, Math.max(0, (v - range.min) / (range.max - range.min))) : 0;
  const angleAt = (fraction: number) => Math.PI * (1 - fraction);
  const pointAt = (radius: number, angle: number) => ({ x: cx + radius * Math.cos(angle), y: cy - radius * Math.sin(angle) });

  const angle = angleAt(toFraction(value));
  const tipX = cx + needleLen * Math.cos(angle);
  const tipY = cy - needleLen * Math.sin(angle);

  const toneColor = (text: string) => {
    const tone = classifyResultTone(text);
    return tone ? toneColors(tone, colors).label : colors.accent;
  };
  // Every band must be visibly its own colour. Tone words give the
  // semantic hue (red/amber/accent), but neighbours often share one --
  // "High" and "Very High" are both red, and a tier set with no tone words
  // at all (PORT's Class I-V, Brain Metastases' "3.4 / 4.7 / 8.8 Months")
  // would paint every band the same accent. A run of same-hue neighbours
  // is shaded light-to-dark along the scale instead: distinct and ordered,
  // without claiming a severity the calculator itself never states.
  const bandColors = range.bands.map((b) => toneColor(b.text));
  const shadedColors = bandColors.map((c, i) => {
    let start = i;
    while (start > 0 && bandColors[start - 1] === c) start--;
    let end = i;
    while (end < bandColors.length - 1 && bandColors[end + 1] === c) end++;
    if (end === start) return c;
    const alpha = Math.round((0.38 + (0.62 * (i - start)) / (end - start)) * 255);
    return c + alpha.toString(16).padStart(2, "0");
  });

  const currentIndex = range.bands.findIndex((b) => value >= b.from && value <= b.to);
  const resolvedNeedleColor = currentIndex >= 0 ? bandColors[currentIndex] : needleColor;

  // The numeric cutoff between two bands (e.g. Aortic Stenosis Risk
  // Score's 7 and 57) is exactly what the user needs to read off the
  // gauge, not just infer from where the color changes -- only when there
  // are few enough of them to label without the numbers overlapping; a
  // 14-rung table (Framingham's risk-% ladder) still gets its full-color
  // arc and its legend below, just not individual tick numbers.
  const showThresholdTicks = range.bands.length >= 2 && range.bands.length <= 6;

  return (
    <View style={{ alignItems: "center", marginTop: 10 }}>
      <View style={{ width: W, height: H }}>
        <Svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          {range.bands.length > 0 ? (
            range.bands.map((b, i) => {
              const p1 = pointAt(r, angleAt(toFraction(b.from)));
              const p2 = pointAt(r, angleAt(toFraction(b.to)));
              return (
                <Path
                  key={i}
                  d={`M ${p1.x} ${p1.y} A ${r} ${r} 0 0 1 ${p2.x} ${p2.y}`}
                  stroke={shadedColors[i]}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  fill="none"
                  opacity={0.92}
                />
              );
            })
          ) : (
            <Path
              d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
              stroke={colors.trackBg}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              fill="none"
            />
          )}
          {showThresholdTicks
            ? range.bands.slice(0, -1).map((b, i) => {
                const tickAngle = angleAt(toFraction(b.to));
                const tickInner = pointAt(r - 7, tickAngle);
                const tickOuter = pointAt(r + 7, tickAngle);
                const labelPoint = pointAt(r + 20, tickAngle);
                return (
                  <React.Fragment key={`tick-${i}`}>
                    <Line x1={tickInner.x} y1={tickInner.y} x2={tickOuter.x} y2={tickOuter.y} stroke={colors.cardBg} strokeWidth={2.5} />
                    <SvgText x={labelPoint.x} y={labelPoint.y + 4} fontSize={10} fontWeight="800" fill={colors.ink} textAnchor="middle">
                      {formatNumber(b.to)}
                    </SvgText>
                  </React.Fragment>
                );
              })
            : null}
          <Line x1={cx} y1={cy} x2={tipX} y2={tipY} stroke={resolvedNeedleColor} strokeWidth={2.5} strokeLinecap="round" />
          <Circle cx={cx} cy={cy} r={5} fill={colors.cardBg} stroke={resolvedNeedleColor} strokeWidth={2.5} />
          <Circle cx={tipX} cy={tipY} r={5.5} fill={resolvedNeedleColor} />
        </Svg>
      </View>
      <View style={{ flexDirection: "row", justifyContent: "space-between", width: W, marginTop: -4 }}>
        {/* An open end has no real number to show (see ResultRange.minOpen)
            -- its outermost cutoff as an inequality instead. Forced LTR:
            in an RTL run the bidi algorithm would mirror "<" into ">". */}
        <AppText weight="700" size={11} muted style={{ writingDirection: "ltr" }}>
          {range.minOpen && range.bands.length > 1 ? `< ${formatNumber(range.bands[0].to)}` : formatNumber(range.min)}
        </AppText>
        <AppText weight="700" size={11} muted style={{ writingDirection: "ltr" }}>
          {range.maxOpen && range.bands.length > 1
            ? `> ${formatNumber(range.bands[range.bands.length - 1].from)}`
            : formatNumber(range.max)}
        </AppText>
      </View>
      {range.bands.length > 0 ? (
        // One band per line, each label wrapping inside the card. A tier's
        // meaning can be a whole sentence (ADviSED's "Clinical
        // Implication"), and laid out as one unbreakable line in a
        // horizontal row it ran straight off the screen. Capped at three
        // lines -- the full text is in that result's own card below.
        <View style={{ alignSelf: "stretch", marginTop: 12, gap: 7 }}>
          {range.bands.map((b, i) => (
            <View key={i} style={{ flexDirection: row, alignItems: "flex-start", gap: 7 }}>
              <View
                style={{ width: 8, height: 8, borderRadius: 999, marginTop: 5, backgroundColor: shadedColors[i], opacity: 0.92 }}
              />
              <AppText
                weight={i === currentIndex ? "800" : "600"}
                size={11.5}
                muted={i !== currentIndex}
                numberOfLines={3}
                style={{ flex: 1, lineHeight: 18, textAlign: isFa ? "right" : "left", writingDirection: isFa ? "rtl" : "ltr" }}
              >
                {stripHtml(isFa ? b.textFa : b.text)}
              </AppText>
            </View>
          ))}
        </View>
      ) : null}
    </View>
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
  onChoose,
}: {
  question: CalculatorQuestion;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  choiceIndex: number | undefined;
  onChoose: (index: number, value: number | undefined) => void;
}) {
  const { colors, shadows } = useTheme();
  const { isFa, row } = useLang();
  const unit = question.units[0];

  const unitFactor = () => {
    const f = unit?.unit_factor !== null && unit?.unit_factor !== undefined ? parseFloat(unit.unit_factor) : 1;
    return Number.isNaN(f) || f === 0 ? 1 : f;
  };

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
            <AppText muted weight="700" size={12}>
              {stripHtml(isFa && unit.title_fa ? unit.title_fa : unit.title)}
            </AppText>
          ) : null}
        </View>
      )}
    </View>
  );
}
