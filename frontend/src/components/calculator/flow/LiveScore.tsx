import React, { useEffect, useMemo, useState } from "react";
import { View } from "react-native";

import { CalculatorDetail } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import {
  CalculatorAnswers,
  ResultRange,
  computeCalculator,
  computeResultRanges,
  extractNumericValue,
} from "@/utils/calculatorEngine";
import { isDisplayedResult, valueKind } from "@/utils/calculatorModel";

import { Chip, TierBar, showTierBar, useTier } from "../common";

const num = (v: string | null | undefined) => (v === null || v === undefined || v === "" ? NaN : parseFloat(v));

/** The answers with every unanswered question filled in neutrally (a choice
 * with its lowest weight, a number with its lowest allowed value), so the
 * score can be shown before all questions are answered. */
function filled(data: CalculatorDetail, answers: CalculatorAnswers, middle = false): CalculatorAnswers {
  const out: CalculatorAnswers = { ...answers };
  for (const q of data.questions) {
    if (out[q.position] !== undefined) continue;
    if (q.type === "multiple_choice") {
      const f = q.choices.map((c) => num(c.answer_factor)).filter((v) => !Number.isNaN(v));
      if (f.length) out[q.position] = middle ? f[Math.floor(f.length / 2)] : Math.min(...f);
    } else if (q.type === "numeric_input") {
      const u = q.units[0];
      const mn = num(u?.min_value);
      const mx = num(u?.max_value);
      const base = !Number.isNaN(mn) ? (middle && !Number.isNaN(mx) ? (mn + mx) / 2 : mn) : 0;
      out[q.position] = base * (u && u.unit_factor ? parseFloat(u.unit_factor) || 1 : 1);
    } else {
      out[q.position] = 0;
    }
  }
  return out;
}

/** The score the answers give so far, with the calculator's own tiers. */
export function useLiveScore(data: CalculatorDetail, answers: CalculatorAnswers) {
  const [range, setRange] = useState<ResultRange | null>(null);

  const primary = useMemo(() => {
    const shown = data.results.filter(isDisplayedResult);
    const computed = computeCalculator(data.questions, data.results, filled(data, {}, true), { stringsFa: data.formula_strings_fa });
    return computed.find((r) => shown.some((s) => s.position === r.position) && valueKind(r.answerText) === "num")?.position ?? null;
  }, [data]);

  // The tiers do not depend on the answers; sweeping them is the slow part,
  // so it runs once, after the first paint.
  useEffect(() => {
    if (primary === null) return;
    const id = setTimeout(() => {
      const ranges = computeResultRanges(data.questions, data.results, filled(data, {}, true), data.formula_strings_fa);
      setRange(ranges.get(primary) ?? null);
    }, 0);
    return () => clearTimeout(id);
  }, [data, primary]);

  const { value, rows } = useMemo(() => {
    if (primary === null) return { value: null, rows: [] };
    const computed = computeCalculator(data.questions, data.results, filled(data, answers), { stringsFa: data.formula_strings_fa });
    const text = computed.find((r) => r.position === primary)?.answerText;
    return { value: text ? extractNumericValue(text) : null, rows: computed };
  }, [data, answers, primary]);

  // `rows` lets the tier be read off its own row where bands meet (see bandFor).
  return { value, range, rows };
}

/** "Score so far": the number, the tier it is in (when the tier has a short
 * name -- a sentence of interpretation waits for the result) and the bar of
 * tiers with a marker, updating with every answer. */
export function LiveScore({ data, answers }: { data: CalculatorDetail; answers: CalculatorAnswers }) {
  const { t, isFa } = useLang();
  const { value, range, rows } = useLiveScore(data, answers);
  const tier = useTier(range ?? undefined, value, rows);
  if (value === null) return null;
  return (
    <Card style={{ gap: 8 }}>
      <View style={{ flexDirection: "row", alignItems: "baseline", justifyContent: "space-between", gap: 8 }}>
        <View style={{ flex: 1 }}>
          <AppText weight="700" size={11.5} muted style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
            {t("calcLiveScore")}
          </AppText>
          <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, direction: "ltr" }}>
            <AppText weight="900" size={30} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 38 }}>
              {Number(value.toFixed(2))}
            </AppText>
            {range && !range.maxOpen ? (
              <AppText weight="700" size={13} muted>
                {t("calcOutOf")} {range.max}
              </AppText>
            ) : null}
          </View>
        </View>
        {tier?.style === "headline" ? (
          <View style={{ maxWidth: "60%" }}>
            <Chip text={tier.text} tone={tier.tone} />
          </View>
        ) : null}
      </View>
      {range && showTierBar(range) ? <TierBar value={value} range={range} active={tier?.band} isFa={isFa} showNames={false} /> : null}
    </Card>
  );
}
