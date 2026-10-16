import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { MeasureValue, parseMeasure, valueKind } from "@/utils/calculatorModel";

import { Chip, Extras, Ltr, ResultCard, ResultProps, TierBar, bandAt, toneOf, useShown } from "./common";

/** A measured quantity: a big number with its unit, a switch between the
 * units the calculator can answer in, and the calculator's own reference
 * tiers when it has them. */
export function MeasureResult({ results, ranges, altResults }: ResultProps) {
  const { isFa } = useLang();
  const { colors } = useTheme();
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "numunit") ?? results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const main = parseMeasure(primary.answerText ?? "");

  // The units on offer: the one the calculator answered in, one written into
  // the same text, and the other unit system's answer when its formula has one.
  const options: MeasureValue[] = [];
  if (main) {
    options.push(main.main, ...main.alts);
    const alt = altResults?.find((r) => r.position === primary.position);
    const altParsed = alt ? parseMeasure(alt.answerText ?? "") : null;
    if (altParsed && !options.some((o) => o.unit === altParsed.main.unit)) options.push(altParsed.main);
  }
  const [picked, setPicked] = useState(0);
  const current = options[Math.min(picked, options.length - 1)];

  const range = ranges.get(primary.position);
  const value = extractNumericValue(primary.answerText ?? "");
  const useTiers = !!range && range.bands.length > 0 && value !== null && picked === 0;
  const band = useTiers && range && value !== null ? bandAt(range.bands, value) : null;
  const bandText = band ? (isFa ? band.textFa || band.text : band.text) : null;
  const tone = band ? toneOf(band.text) : "info";
  const others = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text && r.text !== bandText);

  return (
    <ResultCard title={p.title} tone={tone}>
      <View style={{ flexDirection: "row", alignItems: "baseline", gap: 8, direction: "ltr", flexWrap: "wrap" }}>
        <AppText weight="900" size={42} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 52 }}>
          {current ? current.value : p.text}
        </AppText>
        {current?.unit ? (
          <AppText weight="700" size={16} muted style={{ writingDirection: "ltr", textAlign: "left" }}>
            {current.unit}
          </AppText>
        ) : null}
      </View>
      {options.length > 1 ? (
        <View
          style={{
            flexDirection: "row",
            alignSelf: "flex-start",
            direction: "ltr",
            borderRadius: 999,
            borderWidth: 1,
            borderColor: colors.border,
            backgroundColor: colors.softBg,
            overflow: "hidden",
          }}
        >
          {options.map((o, i) => (
            <Pressable
              key={`${o.unit}-${i}`}
              onPress={() => setPicked(i)}
              style={{ paddingHorizontal: 12, paddingVertical: 5, backgroundColor: i === picked ? colors.accent : "transparent" }}
            >
              <Ltr size={12} color={i === picked ? colors.onAccent : colors.muted}>
                {o.unit || "—"}
              </Ltr>
            </Pressable>
          ))}
        </View>
      ) : null}
      {bandText ? <Chip text={bandText} tone={tone} /> : null}
      {useTiers && range && value !== null ? <TierBar value={value} range={range} isFa={isFa} /> : null}
      <Extras items={others} />
    </ResultCard>
  );
}
