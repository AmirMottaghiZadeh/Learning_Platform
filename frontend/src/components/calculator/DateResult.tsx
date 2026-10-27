import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { GREGORIAN_MONTHS_EN, JALALI_MONTHS_FA, toJalali } from "@/utils/jalali";
import { parseAge, parseDateText, valueKind } from "@/utils/calculatorModel";

import { Ltr, ResultCard, ResultProps, RichLines, Rows, useShown } from "./common";

const FULL_TERM_WEEKS = 40;

/** A date in the calendar the reader uses: Jalali in Persian (with the
 * Gregorian one small underneath), Gregorian in English. */
export function useDateFormat() {
  const { isFa, n } = useLang();
  return (d: { gy: number; gm: number; gd: number }) => {
    const j = toJalali(d.gy, d.gm, d.gd);
    return {
      main: isFa ? `${n(j.jd)} ${JALALI_MONTHS_FA[j.jm - 1]} ${n(j.jy)}` : `${GREGORIAN_MONTHS_EN[d.gm - 1]} ${d.gd}, ${d.gy}`,
      other: isFa ? `${d.gy}-${String(d.gm).padStart(2, "0")}-${String(d.gd).padStart(2, "0")}` : null,
    };
  };
}

/** Dates and gestational ages: the due date large, the age as weeks and
 * days on a pregnancy-length bar, any other date as a row. */
export function DateResult({ results }: ResultProps) {
  const { colors } = useTheme();
  const { isFa, n, t } = useLang();
  const shown = useShown();
  const format = useDateFormat();

  const dates = results.filter((r) => valueKind(r.answerText) === "date");
  const ages = results.filter((r) => valueKind(r.answerText) === "age");
  const others = results.filter((r) => !dates.includes(r) && !ages.includes(r)).map(shown).filter((r) => r.text);
  const hero = dates.find((r) => /due|deliver|edd/i.test(r.title)) ?? dates[0];
  const secondary = dates.filter((r) => r !== hero);

  const ageText = (a: { weeks: number; days: number }) =>
    isFa ? `${n(a.weeks)} ${t("calcWeeks")} ${a.days ? `و ${n(a.days)} ${t("calcDays")}` : ""}`.trim() : `${a.weeks} ${t("calcWeeks")} ${a.days} ${t("calcDays")}`;

  return (
    <>
      {hero ? (
        <ResultCard title={shown(hero).title}>
          {(() => {
            const d = parseDateText(hero.answerText ?? "");
            if (!d) return <AppText weight="900" size={22}>{shown(hero).text}</AppText>;
            const f = format(d);
            return (
              <View style={{ gap: 2 }}>
                <AppText weight="900" size={28} style={{ lineHeight: 40 }}>
                  {f.main}
                </AppText>
                {f.other ? (
                  <Ltr size={12.5} muted weight="600">
                    {f.other} · {t("calcGregorianShort")}
                  </Ltr>
                ) : null}
              </View>
            );
          })()}
          {secondary.length ? (
            <Rows
              rows={secondary.map((r) => {
                const d = parseDateText(r.answerText ?? "");
                return { label: shown(r).title, value: d ? format(d).main : shown(r).text };
              })}
            />
          ) : null}
        </ResultCard>
      ) : null}
      {ages.map((r) => {
        const a = parseAge(r.answerText ?? "");
        if (!a) return null;
        const progress = Math.min(1, (a.weeks + a.days / 7) / FULL_TERM_WEEKS);
        return (
          <ResultCard key={r.position} title={shown(r).title}>
            <AppText weight="900" size={26} style={{ lineHeight: 38 }}>
              {ageText(a)}
            </AppText>
            <View style={{ gap: 4, direction: "ltr" }}>
              <View style={{ height: 10, borderRadius: 5, backgroundColor: colors.trackBg, overflow: "hidden" }}>
                <View style={{ width: `${progress * 100}%`, height: 10, backgroundColor: colors.accent, borderRadius: 5 }} />
              </View>
              <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <Ltr size={10.5} muted weight="600">
                  0
                </Ltr>
                <Ltr size={10.5} muted weight="600">
                  {FULL_TERM_WEEKS} {t("calcWeekAbbr")}
                </Ltr>
              </View>
            </View>
          </ResultCard>
        );
      })}
      {others.map((o, i) => (
        <ResultCard key={i} title={o.title}>
          <RichLines text={o.text} />
        </ResultCard>
      ))}
    </>
  );
}
