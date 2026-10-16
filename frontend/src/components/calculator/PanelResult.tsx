import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { parseMeasure, splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Chip, Extras, Ltr, ResultCard, ResultProps, toneOf, useShown } from "./common";

/** Several results at once: the first number is the headline, the rest sit
 * in one table beneath it (longer text under that). */
export function PanelResult({ results }: ResultProps) {
  const shown = useShown();
  const primary = results.find((r) => ["num", "pct", "numunit"].includes(valueKind(r.answerText))) ?? results[0];
  const p = shown(primary);
  const measure = parseMeasure(primary.answerText ?? "");
  const lead = splitLeadingNumber(primary.answerText ?? "");
  const rest = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text);
  const chips = rest.filter((r) => r.text.length > 28 && r.text.length <= 36 && !r.text.includes("\n"));
  const others = rest.filter((r) => !chips.includes(r));

  return (
    <ResultCard title={p.title} tone={toneOf(`${p.en} ${chips.map((c) => c.en).join(" ")}`)}>
      <View style={{ flexDirection: "row", alignItems: "baseline", gap: 8, direction: "ltr", flexWrap: "wrap" }}>
        <AppText weight="900" size={40} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 50 }}>
          {measure ? measure.main.value : lead ? lead.value : p.text}
        </AppText>
        {measure?.main.unit ? (
          <Ltr size={15} muted>
            {measure.main.unit}
          </Ltr>
        ) : null}
      </View>
      {chips.map((c, i) => (
        <Chip key={i} text={c.text} tone={toneOf(c.en)} />
      ))}
      <Extras items={others} />
    </ResultCard>
  );
}
