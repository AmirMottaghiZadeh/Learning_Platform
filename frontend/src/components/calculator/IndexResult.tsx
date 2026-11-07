import React from "react";

import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, Interpretation, ResultCard, ResultProps, TierBar, showTierBar, toneOf, useShown, useTier } from "./common";

/** An index or ratio: the number centred, what it means (a short tier name in
 * the colour of how serious it is, a longer one in its own box), the decision
 * thresholds the calculator itself applies (its interpretation rows, drawn
 * as tiers), then any explanation below. */
export function IndexResult({ results, ranges }: ResultProps) {
  const { isFa, t } = useLang();
  const shown = useShown();
  const primary = results.find((r) => ["num", "pct", "numunit"].includes(valueKind(r.answerText))) ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "");
  const lead = splitLeadingNumber(isFa ? primary.answerTextFa ?? primary.answerText ?? "" : primary.answerText ?? "");
  const leadEn = splitLeadingNumber(primary.answerText ?? "");
  const range = ranges.get(primary.position);
  const tier = useTier(range, value, results);
  // "12.3 (Probably thalassaemia.)": the parenthesis is the interpretation.
  const inline = lead?.rest.replace(/^\(|\)$/g, "").trim();
  const inlineIsUnit = !!inline && inline.length <= 14 && !/\s/.test(inline);
  const label = tier ? (tier.style === "headline" ? tier.text : null) : inline && !inlineIsUnit ? inline : null;
  const tone = tier ? tier.tone : toneOf(leadEn?.rest ?? "");
  const standIn = tier && tier.style !== "value" ? tier.source : null;
  const others = results
    .filter((r) => r.position !== primary.position && r.position !== standIn)
    .map(shown)
    .filter((r) => r.text && r.text !== label);

  return (
    <ResultCard title={p.title} tone={tier?.style === "callout" ? "info" : tone} center>
      <Hero
        value={lead ? lead.value : p.text}
        unit={inlineIsUnit ? inline : undefined}
        caption={tier?.style === "headline" ? tier.title : null}
        label={label}
        tone={tone}
      />
      {range && range.bands.length > 0 && value !== null && showTierBar(range) ? <TierBar value={value} range={range} active={tier?.band} isFa={isFa} /> : null}
      {tier?.style === "callout" ? (
        <Interpretation title={tier.title ?? t("calcInterpretation")} text={tier.text} tone={tier.tone} />
      ) : null}
      <Explain items={others} />
    </ResultCard>
  );
}
