import React from "react";

import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, Interpretation, ResultCard, ResultProps, TierBar, showTierBar, toneOf, useShown, useTier } from "./common";

/** A clinical score: the number out of its maximum with the tier it falls in
 * (from the calculator's own interpretation rows) -- a short tier name large
 * under the number, coloured by how serious it is, a longer one in its own
 * box -- the bar of all tiers when it says something, and what else the
 * calculator reports below. */
export function ScoreResult({ results, ranges }: ResultProps) {
  const { isFa, t } = useLang();
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "") ?? 0;
  const range = ranges.get(primary.position);
  const tier = useTier(range, value, results);
  const lead = splitLeadingNumber(primary.answerText ?? "");
  // A score with no tiers of its own may still carry its meaning in its text.
  const inline = lead && lead.rest ? lead.rest : null;
  const label = tier ? (tier.style === "headline" ? tier.text : null) : inline;
  const tone = tier ? tier.tone : toneOf(inline ?? "");
  const standIn = tier && tier.style !== "value" ? tier.source : null;
  const others = results
    .filter((r) => r.position !== primary.position && r.position !== standIn)
    .map(shown)
    .filter((r) => r.text && r.text !== label);

  return (
    <ResultCard title={p.title} tone={tier?.style === "callout" ? "info" : tone} center>
      <Hero
        value={lead ? lead.value : p.text}
        suffix={range && !range.maxOpen ? `${t("calcOutOf")} ${range.max}` : undefined}
        caption={tier?.style === "headline" ? tier.title : null}
        label={label}
        tone={tone}
      />
      {range && showTierBar(range) ? <TierBar value={value} range={range} active={tier?.band} isFa={isFa} /> : null}
      {tier?.style === "callout" ? (
        <Interpretation title={tier.title ?? t("calcInterpretation")} text={tier.text} tone={tier.tone} />
      ) : null}
      <Explain items={others} />
    </ResultCard>
  );
}
