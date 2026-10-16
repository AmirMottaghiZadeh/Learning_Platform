import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Chip, Extras, ResultCard, ResultProps, TierBar, bandAt, toneOf, useShown } from "./common";

/** An index or ratio: the number, then the decision thresholds the
 * calculator itself applies (its interpretation rows, drawn as tiers) and
 * what the number means. With no thresholds in the data the card is just the
 * number and its interpretation. */
export function IndexResult({ results, ranges }: ResultProps) {
  const { isFa } = useLang();
  const shown = useShown();
  const primary = results.find((r) => ["num", "pct", "numunit"].includes(valueKind(r.answerText))) ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "");
  const lead = splitLeadingNumber(isFa ? primary.answerTextFa ?? primary.answerText ?? "" : primary.answerText ?? "");
  const leadEn = splitLeadingNumber(primary.answerText ?? "");
  const range = ranges.get(primary.position);
  const hasTiers = !!range && range.bands.length > 0 && value !== null;
  const band = hasTiers && range && value !== null ? bandAt(range.bands, value) : null;
  const bandText = band ? (isFa ? band.textFa || band.text : band.text) : null;
  // "12.3 (Probably thalassaemia.)": the parenthesis is the interpretation.
  const inline = lead?.rest.replace(/^\(|\)$/g, "").trim();
  const inlineIsUnit = !!inline && inline.length <= 14 && !/\s/.test(inline);
  const interpretation = bandText ?? (inline && !inlineIsUnit ? inline : null);
  const tone = toneOf(`${band?.text ?? ""} ${leadEn?.rest ?? ""}`);
  const others = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text && r.text !== interpretation);

  return (
    <ResultCard title={p.title} tone={tone}>
      <View style={{ flexDirection: "row", alignItems: "baseline", gap: 8, direction: "ltr" }}>
        <AppText weight="900" size={42} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 52 }}>
          {lead ? lead.value : p.text}
        </AppText>
        {inlineIsUnit ? (
          <AppText weight="700" size={14} muted style={{ writingDirection: "ltr", textAlign: "left" }}>
            {inline}
          </AppText>
        ) : null}
      </View>
      {interpretation ? <Chip text={interpretation} tone={tone} /> : null}
      {hasTiers && range && value !== null ? <TierBar value={value} range={range} isFa={isFa} /> : null}
      <Extras items={others} />
    </ResultCard>
  );
}
