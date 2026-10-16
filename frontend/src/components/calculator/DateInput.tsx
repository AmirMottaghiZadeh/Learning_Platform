import React, { useEffect, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { CalculatorQuestion } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { stripHtml } from "@/utils/html";
import {
  GREGORIAN_MONTHS_EN,
  JALALI_MONTHS_FA,
  dateToMs,
  isValidGregorian,
  isValidJalali,
  msToGregorian,
  toGregorian,
  toJalali,
} from "@/utils/jalali";

const DAY_MS = 86_400_000;

function QuestionTitle({ question }: { question: CalculatorQuestion }) {
  const { isFa } = useLang();
  return (
    <>
      <AppText weight="700" size={13.5} style={{ lineHeight: 20, writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}>
        {stripHtml(isFa && question.title_fa ? question.title_fa : question.title)}
      </AppText>
      {question.more_information || question.more_information_fa ? (
        <AppText muted weight="600" size={12} style={{ marginTop: 3, lineHeight: 18, writingDirection: isFa ? "rtl" : "ltr", textAlign: isFa ? "right" : "left" }}>
          {stripHtml(isFa && question.more_information_fa ? question.more_information_fa : question.more_information ?? "")}
        </AppText>
      ) : null}
    </>
  );
}

function Field({
  label,
  value,
  onChange,
  width,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  width: number;
  placeholder: string;
}) {
  const { colors } = useTheme();
  return (
    <View style={{ width, gap: 3 }}>
      <AppText weight="700" size={10.5} muted center>
        {label}
      </AppText>
      <TextInput
        value={value}
        onChangeText={(v) => onChange(v.replace(/[^\d]/g, ""))}
        keyboardType="number-pad"
        selectTextOnFocus
        autoComplete="off"
        autoCorrect={false}
        textContentType="none"
        importantForAutofill="no"
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        style={{
          fontFamily: fontFamily("700"),
          fontSize: 15,
          color: colors.ink,
          textAlign: "center",
          writingDirection: "ltr",
          paddingVertical: 10,
          paddingHorizontal: 4,
          borderRadius: 12,
          borderWidth: 1,
          borderColor: colors.trackBg,
          backgroundColor: colors.inputBg,
        }}
      />
    </View>
  );
}

/** A calendar date, typed as year / month / day in the calendar the reader
 * uses (Jalali in Persian, Gregorian in English). It hands the engine the
 * date as the timestamp the source formulas expect, and nothing at all while
 * the fields don't make a real date. */
export function DateInput({
  question,
  value,
  onChange,
}: {
  question: CalculatorQuestion;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
}) {
  const { colors } = useTheme();
  const { isFa, t, n } = useLang();
  const initial = () => {
    if (value === undefined) return { y: "", m: "", d: "" };
    const g = msToGregorian(value);
    if (!isFa) return { y: String(g.gy), m: String(g.gm), d: String(g.gd) };
    const j = toJalali(g.gy, g.gm, g.gd);
    return { y: String(j.jy), m: String(j.jm), d: String(j.jd) };
  };
  const [parts, setParts] = useState(initial);

  const apply = (next: { y: string; m: string; d: string }) => {
    setParts(next);
    const y = Number(next.y);
    const m = Number(next.m);
    const d = Number(next.d);
    if (!next.y || !next.m || !next.d || next.y.length < 4) return onChange(undefined);
    if (isFa) {
      if (!isValidJalali(y, m, d)) return onChange(undefined);
      const g = toGregorian(y, m, d);
      return onChange(dateToMs(g.gy, g.gm, g.gd));
    }
    if (!isValidGregorian(y, m, d)) return onChange(undefined);
    onChange(dateToMs(y, m, d));
  };

  const today = () => {
    const now = new Date();
    const g = { gy: now.getFullYear(), gm: now.getMonth() + 1, gd: now.getDate() };
    if (!isFa) return apply({ y: String(g.gy), m: String(g.gm), d: String(g.gd) });
    const j = toJalali(g.gy, g.gm, g.gd);
    apply({ y: String(j.jy), m: String(j.jm), d: String(j.jd) });
  };

  // Questions that ask for "today" start filled in.
  useEffect(() => {
    if (value === undefined && /current date|today|date of (evaluation|assessment)/i.test(question.title)) today();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filled = !!parts.y && !!parts.m && !!parts.d && parts.y.length >= 4;
  const invalid = filled && value === undefined;
  const monthName = (() => {
    const m = Number(parts.m);
    if (!m || m < 1 || m > 12) return "";
    return isFa ? JALALI_MONTHS_FA[m - 1] : GREGORIAN_MONTHS_EN[m - 1];
  })();
  const other = value !== undefined && isFa ? (() => {
    const g = msToGregorian(value);
    return `${g.gy}-${String(g.gm).padStart(2, "0")}-${String(g.gd).padStart(2, "0")} · ${t("calcGregorianShort")}`;
  })() : null;

  return (
    <View>
      <QuestionTitle question={question} />
      <View style={{ flexDirection: "row", direction: "ltr", alignItems: "flex-end", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
        <Field label={t("calcYear")} value={parts.y} onChange={(v) => apply({ ...parts, y: v.slice(0, 4) })} width={84} placeholder={isFa ? "1405" : "2026"} />
        <Field label={t("calcMonth")} value={parts.m} onChange={(v) => apply({ ...parts, m: v.slice(0, 2) })} width={62} placeholder="MM" />
        <Field label={t("calcDay")} value={parts.d} onChange={(v) => apply({ ...parts, d: v.slice(0, 2) })} width={62} placeholder="DD" />
        <Pressable
          onPress={today}
          style={{ paddingHorizontal: 14, paddingVertical: 11, borderRadius: 12, borderWidth: 1, borderColor: colors.accent, backgroundColor: `${colors.accent}14` }}
        >
          <AppText weight="800" size={12.5} color={colors.accent}>
            {t("calcToday")}
          </AppText>
        </Pressable>
      </View>
      {monthName ? (
        <AppText weight="700" size={12} muted style={{ marginTop: 6 }}>
          {monthName}
          {value !== undefined && isFa ? ` ${n(parts.y)}` : ""}
        </AppText>
      ) : null}
      {other ? (
        <AppText weight="600" size={11.5} muted style={{ writingDirection: "ltr", textAlign: "left" }}>
          {other}
        </AppText>
      ) : null}
      {invalid ? (
        <AppText weight="700" size={12} color={colors.denyLabel} style={{ marginTop: 4 }}>
          {t("calcInvalidDate")}
        </AppText>
      ) : null}
    </View>
  );
}

/** A length of time in weeks and days (an ultrasound's gestational age),
 * handed over as milliseconds like the source formulas expect. */
export function DaysInput({
  question,
  value,
  onChange,
}: {
  question: CalculatorQuestion;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
}) {
  const { t } = useLang();
  const initial = () => {
    if (value === undefined) return { w: "", d: "" };
    const days = Math.round(value / DAY_MS);
    return { w: String(Math.floor(days / 7)), d: String(days % 7) };
  };
  const [parts, setParts] = useState(initial);
  const apply = (next: { w: string; d: string }) => {
    setParts(next);
    if (!next.w && !next.d) return onChange(undefined);
    onChange(((Number(next.w) || 0) * 7 + (Number(next.d) || 0)) * DAY_MS);
  };
  return (
    <View>
      <QuestionTitle question={question} />
      <View style={{ flexDirection: "row", direction: "ltr", gap: 8, marginTop: 10 }}>
        <Field label={t("calcWeeks")} value={parts.w} onChange={(v) => apply({ ...parts, w: v.slice(0, 2) })} width={84} placeholder="0" />
        <Field label={t("calcDays")} value={parts.d} onChange={(v) => apply({ ...parts, d: v.slice(0, 1) })} width={62} placeholder="0" />
      </View>
    </View>
  );
}
