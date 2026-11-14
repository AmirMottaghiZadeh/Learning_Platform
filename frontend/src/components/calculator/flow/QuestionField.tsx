import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { CalculatorQuestion } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { unitFactorOf } from "@/utils/calculatorEngine";
import { stripHtml } from "@/utils/html";
import { UnitSystem, calculatorLabel, choiceDisplay, choiceLabels } from "@/utils/calculatorLabels";
import { parseTypedNumber } from "@/utils/typedNumber";

import { DateInput, DaysInput } from "../DateInput";

/** `card`: one question on its own screen, large. `row`: one line of a list
 * of questions, compact. */
export type FieldVariant = "card" | "row";

export interface FieldProps {
  question: CalculatorQuestion;
  variant: FieldVariant;
  value: number | undefined;
  choiceIndex: number | undefined;
  unitIndex: number;
  onChange: (value: number | undefined) => void;
  onChoose: (index: number, value: number | undefined) => void;
  onUnit: (index: number) => void;
  /** Each choice's effect on the score (+3, -4), shown beside it -- for
   * scores; see choiceWeights. Null or absent: no weights. */
  weights?: (number | null)[] | null;
  /** The calculator's SI/US switch: a choice written in both shows only
   * this one. Null or absent: both, the second under the first. */
  unitSystem?: UnitSystem | null;
}

/** A yes/no style question: two short choices. */
export function isBinaryQuestion(question: CalculatorQuestion, isFa: boolean) {
  return (
    question.type === "multiple_choice" &&
    question.choices.length === 2 &&
    question.choices.every((c) => {
      const labels = choiceLabels(c, isFa);
      return labels.length === 1 && labels[0].length <= 22;
    })
  );
}

function label(question: CalculatorQuestion, isFa: boolean) {
  return calculatorLabel(isFa && question.title_fa ? question.title_fa : question.title, isFa);
}

function Weight({ factor }: { factor: number }) {
  const { colors } = useTheme();
  if (Number.isNaN(factor)) return null;
  return (
    <AppText weight="800" size={11.5} color={colors.muted} style={{ writingDirection: "ltr", textAlign: "left" }}>
      {factor > 0 ? `+${factor}` : String(factor)}
    </AppText>
  );
}

/** A choice's label, and under it the second label (another unit or an
 * explanation) a little smaller and lighter, so the first one leads. */
function ChoiceText({ main, sub, size, weight, color, style }: {
  main: string;
  sub: string | null;
  size: number;
  weight: "700" | "800" | "900";
  color: string;
  style?: object;
}) {
  const { colors } = useTheme();
  return (
    <View style={[{ gap: 2 }, style]}>
      <AppText weight={weight} size={size} color={color} style={{ lineHeight: Math.round(size * 1.55) }}>
        {main}
      </AppText>
      {sub ? (
        <AppText weight="600" size={size - 2} color={colors.muted} style={{ lineHeight: Math.round((size - 2) * 1.55) }}>
          {sub}
        </AppText>
      ) : null}
    </View>
  );
}

function Choices({ question, variant, value, choiceIndex, onChoose, weights, unitSystem }: FieldProps) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const options = question.choices.map((choice, i) => {
    const factor = choice.answer_factor !== null ? parseFloat(choice.answer_factor) : NaN;
    const { main, sub } = choiceDisplay(choice, isFa, unitSystem ?? null);
    return {
      i,
      factor,
      main,
      sub,
      selected: choiceIndex === i && value !== undefined,
      weight: weights?.[i] ?? null,
    };
  });
  const pick = (o: (typeof options)[number]) => onChoose(o.i, Number.isNaN(o.factor) ? undefined : o.factor);
  const binary = isBinaryQuestion(question, isFa);

  if (variant === "row") {
    if (binary) {
      return (
        <View style={{ flexDirection: row, borderRadius: 999, borderWidth: 1, borderColor: colors.border, overflow: "hidden", backgroundColor: colors.softBg }}>
          {options.map((o) => (
            <Pressable key={o.i} onPress={() => pick(o)} style={{ paddingHorizontal: 14, paddingVertical: 6, backgroundColor: o.selected ? colors.accent : "transparent" }}>
              <AppText weight="800" size={12} color={o.selected ? colors.onAccent : colors.muted}>
                {o.main}
              </AppText>
            </Pressable>
          ))}
        </View>
      );
    }
    return (
      <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6 }}>
        {options.map((o) => (
          <Pressable
            key={o.i}
            onPress={() => pick(o)}
            style={{
              paddingHorizontal: 12,
              paddingVertical: 6,
              maxWidth: "100%",
              width: o.sub ? "100%" : undefined,
              borderRadius: o.sub ? 12 : 999,
              borderWidth: 1,
              borderColor: o.selected ? colors.accent : colors.trackBg,
              backgroundColor: o.selected ? `${colors.accent}1a` : colors.softBg,
            }}
          >
            <ChoiceText main={o.main} sub={o.sub} size={12} weight="700" color={o.selected ? colors.accent : colors.ink} />
          </Pressable>
        ))}
      </View>
    );
  }

  if (binary) {
    return (
      <View style={{ flexDirection: row, gap: 10 }}>
        {options.map((o) => (
          <Pressable
            key={o.i}
            onPress={() => pick(o)}
            style={{
              flex: 1,
              alignItems: "center",
              justifyContent: "center",
              paddingVertical: 22,
              borderRadius: 16,
              borderWidth: 1.5,
              borderColor: o.selected ? colors.accent : colors.trackBg,
              backgroundColor: o.selected ? `${colors.accent}1a` : colors.cardBg,
              gap: 2,
            }}
          >
            <ChoiceText
              main={o.main}
              sub={o.sub}
              size={17}
              weight="900"
              color={o.selected ? colors.accent : colors.ink}
              style={{ alignItems: "center" }}
            />
            {o.weight !== null ? <Weight factor={o.weight} /> : null}
          </Pressable>
        ))}
      </View>
    );
  }

  return (
    <View style={{ gap: 8 }}>
      {options.map((o) => (
        <Pressable
          key={o.i}
          onPress={() => pick(o)}
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 10,
            paddingHorizontal: 14,
            paddingVertical: 13,
            borderRadius: 16,
            borderWidth: 1.5,
            borderColor: o.selected ? colors.accent : colors.trackBg,
            backgroundColor: o.selected ? `${colors.accent}1a` : colors.cardBg,
          }}
        >
          <View
            style={{
              width: 20,
              height: 20,
              borderRadius: 10,
              borderWidth: 2,
              borderColor: o.selected ? colors.accent : colors.trackBg,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {o.selected ? <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: colors.accent }} /> : null}
          </View>
          <ChoiceText
            main={o.main}
            sub={o.sub}
            size={14}
            weight="700"
            color={o.selected ? colors.accent : colors.ink}
            style={{ flex: 1, writingDirection: isFa ? "rtl" : "ltr" }}
          />
          {o.weight !== null ? <Weight factor={o.weight} /> : null}
        </Pressable>
      ))}
    </View>
  );
}

function Numeric({ question, variant, value, unitIndex, onChange, onUnit }: FieldProps) {
  const { colors } = useTheme();
  const { isFa, t } = useLang();
  const unit = question.units[unitIndex] ?? question.units[0];
  const factor = () => unitFactorOf(unit);
  // The input shows what was typed, in the chosen unit; `value` is already
  // multiplied by unit_factor for the formulas, so the field is not controlled
  // from it (it is only the starting text, for a question revisited).
  const [text, setText] = useState(() => (value === undefined ? "" : String(Number((value / factor()).toFixed(6)))));
  const big = variant === "card";
  // Typed but not a number: say so, instead of a Next button that stays off.
  const invalid = text.trim() !== "" && Number.isNaN(parseTypedNumber(text));

  return (
    <View style={{ gap: 10 }}>
      <View
        style={{
          // The number, then its unit on the right, in both languages.
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
          backgroundColor: colors.inputBg,
          borderWidth: big ? 1.5 : 1,
          borderColor: big && value !== undefined ? colors.accent : colors.trackBg,
          borderRadius: big ? 16 : 12,
          paddingHorizontal: big ? 16 : 10,
          paddingVertical: big ? 12 : 6,
          minWidth: big ? undefined : 110,
        }}
      >
        <TextInput
          value={text}
          onChangeText={(next) => {
            setText(next);
            const num = parseTypedNumber(next);
            if (Number.isNaN(num)) return onChange(undefined);
            onChange(num * factor());
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
            // An input has a width of its own (about twenty characters); without
            // this it would not shrink and would push the unit out of the box.
            minWidth: 0,
            fontFamily: fontFamily(big ? "800" : "700"),
            fontSize: big ? 30 : 15,
            color: colors.ink,
            textAlign: "left",
            writingDirection: "ltr",
            padding: 0,
          }}
        />
        {unit ? (
          <AppText muted weight="700" size={big ? 14 : 12} style={{ textAlign: "left", writingDirection: "ltr", flexShrink: 0 }}>
            {stripHtml(isFa && unit.title_fa ? unit.title_fa : unit.title)}
          </AppText>
        ) : null}
      </View>
      {invalid ? (
        <AppText weight="700" size={12} color={colors.denyLabel} style={{ writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}>
          {t("calcInvalidNumber")}
        </AppText>
      ) : null}
      {big && (unit?.min_value || unit?.max_value) ? (
        <AppText muted weight="600" size={11.5} style={{ writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}>
          {t("calcAllowed")}:{" "}
          <AppText weight="700" size={11.5} muted>
            {calculatorLabel([unit?.min_value ? Number(unit.min_value) : "", unit?.max_value ? Number(unit.max_value) : ""].join(" – ").replace(/^ – (.+)$/, "≤ $1").replace(/^(.+) – $/, "≥ $1"), isFa)}
            {unit ? ` ${stripHtml(isFa && unit.title_fa ? unit.title_fa : unit.title)}` : ""}
          </AppText>
        </AppText>
      ) : null}
      {question.units.length > 1 ? (
        <View
          style={{
            flexDirection: "row",
            alignSelf: "flex-start",
            borderRadius: 999,
            borderWidth: 1,
            borderColor: colors.border,
            backgroundColor: colors.softBg,
            overflow: "hidden",
          }}
        >
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
                style={{ paddingHorizontal: 14, paddingVertical: big ? 7 : 5, backgroundColor: selected ? colors.accent : "transparent" }}
              >
                <AppText weight="800" size={12} color={selected ? colors.onAccent : colors.muted} style={{ writingDirection: "ltr", textAlign: "left" }}>
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

/** One question's answer control, in the layout the flow asks for. Dates and
 * week/day counts bring their own title. */
export function QuestionField(props: FieldProps) {
  const { question, variant } = props;
  const { isFa } = useLang();
  if (question.type === "date_input") {
    return <DateInput key={`${question.position}-${isFa}`} question={question} value={props.value} onChange={props.onChange} />;
  }
  if (question.type === "days_input") {
    return <DaysInput question={question} value={props.value} onChange={props.onChange} />;
  }
  const help = calculatorLabel(isFa && question.more_information_fa ? question.more_information_fa : question.more_information ?? "", isFa);
  const card = variant === "card";
  const title = (
    <View style={{ gap: 3, flex: 1 }}>
      <AppText
        weight={card ? "900" : "700"}
        size={card ? 19 : 13}
        style={{ lineHeight: card ? 32 : 21, writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}
      >
        {label(question, isFa)}
      </AppText>
      {help ? (
        <AppText muted weight="600" size={12} style={{ lineHeight: 19, writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}>
          {help}
        </AppText>
      ) : null}
    </View>
  );
  // In a list, a yes/no question is the text with its switch beside it.
  if (!card && isBinaryQuestion(question, isFa)) {
    return (
      <View style={{ flexDirection: isFa ? "row-reverse" : "row", alignItems: "center", gap: 10 }}>
        {title}
        <Choices {...props} />
      </View>
    );
  }
  return (
    <View style={{ gap: card ? 12 : 8 }}>
      {title}
      {question.type === "multiple_choice" ? <Choices {...props} /> : <Numeric {...props} />}
    </View>
  );
}
