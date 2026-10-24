import React from "react";

import { parseMeasure, splitLeadingNumber, valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, ResultCard, ResultProps, toneOf, useShown } from "./common";

/** Several results at once: the first number is the headline (centred, with
 * a short verdict under it in its colour), the rest sit in one table beneath. */
export function PanelResult({ results }: ResultProps) {
  const shown = useShown();
  const primary = results.find((r) => ["num", "pct", "numunit"].includes(valueKind(r.answerText))) ?? results[0];
  const p = shown(primary);
  const measure = parseMeasure(primary.answerText ?? "");
  const lead = splitLeadingNumber(primary.answerText ?? "");
  const rest = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text);
  const verdict = rest.find((r) => valueKind(r.en) === "label" && r.text.length <= 36 && !r.text.includes("\n"));
  const explain = rest.filter((r) => r !== verdict);
  const tone = toneOf(`${p.en} ${verdict?.en ?? ""}`);

  return (
    <ResultCard title={p.title} tone={tone} center>
      <Hero
        value={measure ? measure.main.value : lead ? lead.value : p.text}
        unit={measure?.main.unit}
        label={verdict?.text}
        tone={tone}
        size={42}
      />
      <Explain items={explain} />
    </ResultCard>
  );
}
