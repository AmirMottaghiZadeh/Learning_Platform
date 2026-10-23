import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { MeasureValue, parseMeasure, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, Interpretation, Ltr, ResultCard, ResultProps, TierBar, showTierBar, useShown, useTier } from "./common";

/** A measured quantity: the number with its unit centred, a switch between
 * the units the calculator can answer in, its reference tier (a short name
 * in the colour of how serious it is, a longer one in its own box) and the
 * tier bar, then any explanation. */
export function MeasureResult({ results, ranges, altResults }: ResultProps) {
  const { isFa, t } = useLang();
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
  const tier = useTier(useTiers ? range : undefined, value, results);
  const label = tier?.style === "headline" ? tier.text : null;
  const tone = tier ? tier.tone : "info";
  const standIn = tier && tier.style !== "value" ? tier.source : null;
  const others = results
    .filter((r) => r.position !== primary.position && r.position !== standIn)
    .map(shown)
    .filter((r) => r.text && r.text !== label);

  return (
    <ResultCard title={p.title} tone={tier?.style === "callout" ? "info" : tone} center>
      <Hero
        value={current ? current.value : p.text}
        unit={current?.unit}
        caption={tier?.style === "headline" ? tier.title : null}
        label={label}
        tone={tone}
      />
      {options.length > 1 ? (
        <View
          style={{
            flexDirection: "row",
            alignSelf: "center",
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
      {useTiers && range && value !== null && showTierBar(range) ? <TierBar value={value} range={range} active={tier?.band} isFa={isFa} /> : null}
      {tier?.style === "callout" ? (
        <Interpretation title={tier.title ?? t("calcInterpretation")} text={tier.text} tone={tier.tone} />
      ) : null}
      <Explain items={others} />
    </ResultCard>
  );
}
