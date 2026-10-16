import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Chip, Extras, ResultCard, ResultProps, TierBar, bandAt, toneOf, useShown } from "./common";

/** A clinical score: the number out of its maximum, the tier it falls in
 * (from the calculator's own interpretation rows) and a bar of all the tiers
 * with a marker. Other results (a risk, a sentence) sit underneath. */
export function ScoreResult({ results, ranges }: ResultProps) {
  const { isFa, t } = useLang();
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "") ?? 0;
  const range = ranges.get(primary.position);
  const band = range ? bandAt(range.bands, value) : null;
  const tierText = band ? (isFa ? band.textFa || band.text : band.text) : null;
  const tone = band ? toneOf(band.text) : "info";
  const others = results
    .filter((r) => r.position !== primary.position)
    .map(shown)
    .filter((r) => r.text && r.text !== tierText);
  const lead = splitLeadingNumber(primary.answerText ?? "");

  return (
    <ResultCard title={p.title} tone={tone}>
      <View style={{ flexDirection: "row", alignItems: "baseline", gap: 8, direction: "ltr" }}>
        <AppText weight="900" size={42} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 52 }}>
          {lead ? lead.value : p.text}
        </AppText>
        {range && !range.maxOpen ? (
          <AppText weight="700" size={14} muted>
            {t("calcOutOf")} {range.max}
          </AppText>
        ) : null}
      </View>
      {tierText ? <Chip text={tierText} tone={tone} /> : lead && lead.rest ? <Chip text={lead.rest} tone="info" /> : null}
      {range ? <TierBar value={value} range={range} isFa={isFa} /> : null}
      <Extras items={others} />
    </ResultCard>
  );
}
