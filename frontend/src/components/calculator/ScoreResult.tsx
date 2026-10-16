import React from "react";

import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, ResultCard, ResultProps, TierBar, bandAt, tiersTones, toneOf, useShown } from "./common";

/** A clinical score: the number out of its maximum with the tier it falls in
 * (from the calculator's own interpretation rows) centred and coloured by how
 * serious the tier is, the bar of all tiers, and what else it says below. */
export function ScoreResult({ results, ranges }: ResultProps) {
  const { isFa, t } = useLang();
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "") ?? 0;
  const range = ranges.get(primary.position);
  const band = range ? bandAt(range.bands, value) : null;
  const tierText = band ? (isFa ? band.textFa || band.text : band.text) : null;
  const tone = band && range ? tiersTones(range.bands.map((b) => b.text))[range.bands.indexOf(band)] : "info";
  const others = results
    .filter((r) => r.position !== primary.position)
    .map(shown)
    .filter((r) => r.text && r.text !== tierText);
  const lead = splitLeadingNumber(primary.answerText ?? "");
  // A score with no tiers of its own may still carry its meaning in its text.
  const label = tierText ?? (lead && lead.rest ? lead.rest : null);
  const labelTone = tierText ? tone : toneOf(label ?? "");

  return (
    <ResultCard title={p.title} tone={labelTone} center>
      <Hero
        value={lead ? lead.value : p.text}
        suffix={range && !range.maxOpen ? `${t("calcOutOf")} ${range.max}` : undefined}
        label={label}
        tone={labelTone}
      />
      {range ? <TierBar value={value} range={range} isFa={isFa} /> : null}
      <Explain items={others} />
    </ResultCard>
  );
}
