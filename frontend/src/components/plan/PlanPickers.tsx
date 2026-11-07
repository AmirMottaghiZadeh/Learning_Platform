import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_SHORT } from "@/i18n/strings";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { LessonCategory } from "@/utils/lessonCategories";
import {
  currentJalaliYear,
  daysUntil,
  formatDay,
  isoDay,
  isoFromJalali,
  monthsFromToday,
  parseIsoDay,
} from "@/utils/planDates";
import { toJalali } from "@/utils/jalali";

/** The study plan's inputs, shared by the onboarding plan step and the
 * plan editor (PlanningSetupScreen): exam date, daily minutes, study days
 * and this term's subjects. */

function Chip({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      hitSlop={4}
      style={{
        minHeight: 40,
        paddingHorizontal: 14,
        borderRadius: 999,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: selected ? colors.accent : colors.cardBg,
        borderWidth: 1,
        borderColor: selected ? colors.accent : colors.trackBg,
      }}
    >
      <AppText weight={selected ? "800" : "700"} size={13} color={selected ? colors.onAccent : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );
}

function ChipRow({ children }: { children: React.ReactNode }) {
  const { row } = useLang();
  return <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>{children}</View>;
}

const PRESET_MONTHS = [1, 2, 3, 6];
const latin = (text: string) => text.replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d))).replace(/[^\d]/g, "");

function DateField({
  label,
  value,
  onChange,
  width,
  maxLength,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  width: number;
  maxLength: number;
}) {
  const { colors } = useTheme();
  const { n } = useLang();
  return (
    <View style={{ width, gap: 4 }}>
      <AppText weight="700" size={11} muted center>
        {label}
      </AppText>
      <TextInput
        // kept in Latin digits, shown in the language's own
        value={value ? n(value) : ""}
        onChangeText={(v) => onChange(latin(v))}
        keyboardType="number-pad"
        maxLength={maxLength}
        accessibilityLabel={label}
        style={{
          height: 46,
          borderRadius: 12,
          borderWidth: 1,
          borderColor: colors.trackBg,
          backgroundColor: colors.inputBg,
          textAlign: "center",
          fontFamily: fontFamily("700"),
          fontSize: 16,
          color: colors.ink,
          padding: 0,
        }}
      />
    </View>
  );
}

/** The exam day: a month or more away in one tap, or typed exactly (a
 * Jalali date in Persian, a Gregorian one in English). `onChange(null)`
 * while the typed date is not a real day after today. */
export function ExamDatePicker({ value, onChange }: { value: string | null; onChange: (iso: string | null) => void }) {
  const { isFa, n, row } = useLang();
  const { colors } = useTheme();
  const [preset, setPreset] = useState<number | "exact" | null>(value ? "exact" : null);
  const [parts, setParts] = useState(() => {
    if (!value) return { y: String(isFa ? currentJalaliYear() : new Date().getFullYear()), m: "", d: "" };
    const date = parseIsoDay(value);
    if (!isFa) return { y: String(date.getFullYear()), m: String(date.getMonth() + 1), d: String(date.getDate()) };
    const { jy, jm, jd } = toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate());
    return { y: String(jy), m: String(jm), d: String(jd) };
  });

  const choosePreset = (months: number) => {
    setPreset(months);
    onChange(monthsFromToday(months));
  };
  const setPart = (key: "y" | "m" | "d", v: string) => {
    const next = { ...parts, [key]: v };
    setParts(next);
    const [y, m, d] = [Number(next.y), Number(next.m), Number(next.d)];
    let iso: string | null = null;
    if (isFa) iso = isoFromJalali(y, m, d);
    else if (y && m && d) {
      const date = new Date(y, m - 1, d, 12);
      iso = date.getMonth() === m - 1 && date.getDate() === d ? isoDay(date) : null;
    }
    onChange(iso && daysUntil(iso) > 0 ? iso : null);
  };

  const left = value ? daysUntil(value) : 0;
  return (
    <View style={{ gap: 12 }}>
      <ChipRow>
        {PRESET_MONTHS.map((m) => (
          <Chip key={m} label={isFa ? `${n(m)} ماه دیگر` : `In ${m} month${m > 1 ? "s" : ""}`} selected={preset === m} onPress={() => choosePreset(m)} />
        ))}
        <Chip label={isFa ? "تاریخ دقیق" : "Exact date"} selected={preset === "exact"} onPress={() => { setPreset("exact"); setPart("d", parts.d); }} />
      </ChipRow>
      {preset === "exact" ? (
        <View style={{ flexDirection: row, gap: 10, justifyContent: "flex-start" }}>
          <DateField label={isFa ? "روز" : "Day"} value={parts.d} onChange={(v) => setPart("d", v)} width={64} maxLength={2} />
          <DateField label={isFa ? "ماه" : "Month"} value={parts.m} onChange={(v) => setPart("m", v)} width={64} maxLength={2} />
          <DateField label={isFa ? "سال" : "Year"} value={parts.y} onChange={(v) => setPart("y", v)} width={86} maxLength={4} />
        </View>
      ) : null}
      {value ? (
        <AppText weight="800" size={13} color={colors.accent}>
          {isFa
            ? `${formatDay(value, true, n)}، ${n(left)} روز دیگر`
            : `${formatDay(value, false, n)}, in ${left} day${left === 1 ? "" : "s"}`}
        </AppText>
      ) : preset === "exact" ? (
        <AppText weight="600" size={12} muted>
          {isFa ? "یک تاریخ واقعی بعد از امروز بنویس." : "Enter a real date after today."}
        </AppText>
      ) : null}
    </View>
  );
}

/** Minutes a day, as a few round choices. */
export function MinutesPicker({ value, onChange, options }: { value: number; onChange: (v: number) => void; options: number[] }) {
  const { isFa, n } = useLang();
  return (
    <ChipRow>
      {options.map((m) => (
        <Chip key={m} label={isFa ? `${n(m)} دقیقه` : `${m} min`} selected={value === m} onPress={() => onChange(m)} />
      ))}
    </ChipRow>
  );
}

/** The week's study days, Saturday first. */
export function StudyDaysPicker({ value, onChange }: { value: boolean[]; onChange: (v: boolean[]) => void }) {
  const { lang, row } = useLang();
  const { colors } = useTheme();
  return (
    <View style={{ flexDirection: row, justifyContent: "space-between" }}>
      {DAY_LABELS_SHORT[lang].map((label, i) => {
        const on = value[i];
        return (
          <Pressable
            key={i}
            onPress={() => onChange(value.map((v, j) => (j === i ? !v : v)))}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: on }}
            style={{
              width: 42,
              height: 42,
              borderRadius: 14,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: on ? colors.accent : colors.cardBg,
              borderWidth: 1,
              borderColor: on ? colors.accent : colors.trackBg,
            }}
          >
            <AppText weight="800" size={13} color={on ? colors.onAccent : colors.muted}>
              {label}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

/** This term's subjects, as the lesson categories. */
export function CategoryPicker({
  categories,
  value,
  onChange,
}: {
  categories: LessonCategory[];
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const { isFa } = useLang();
  return (
    <ChipRow>
      {categories.map((c) => {
        const on = value.includes(c.code);
        return (
          <Chip
            key={c.code}
            label={isFa ? c.name_fa : c.name_en}
            selected={on}
            onPress={() => onChange(on ? value.filter((k) => k !== c.code) : [...value, c.code])}
          />
        );
      })}
    </ChipRow>
  );
}
