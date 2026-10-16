import React from "react";

import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, ResultCard, ResultProps, TierBar, bandAt, tiersTones, toneOf, useShown } from "./common";

/** An index or ratio: the number centred, what it means in the colour of how
 * serious that is, the decision thresholds the calculator itself applies
 * (its interpretation rows, drawn as tiers), then any explanation below. */
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
  const tone =
    band && range ? tiersTones(range.bands.map((b) => b.text))[range.bands.indexOf(band)] : toneOf(leadEn?.rest ?? "");
  const others = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text && r.text !== interpretation);

  return (
    <ResultCard title={p.title} tone={tone} center>
      <Hero value={lead ? lead.value : p.text} unit={inlineIsUnit ? inline : undefined} label={interpretation} tone={tone} />
      {hasTiers && range && value !== null ? <TierBar value={value} range={range} isFa={isFa} /> : null}
      <Explain items={others} />
    </ResultCard>
  );
}
