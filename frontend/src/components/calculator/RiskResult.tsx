import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { useTheme } from "@/theme/ThemeProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { valueKind } from "@/utils/calculatorModel";

import { Chip, Extras, Ltr, ResultCard, ResultProps, Rows, toneOf, useShown } from "./common";

function Ring({ percent, label }: { percent: number; label: string }) {
  const { colors } = useTheme();
  const size = 132;
  const r = 50;
  const c = 2 * Math.PI * r;
  const filled = (Math.max(0, Math.min(100, percent)) / 100) * c;
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} viewBox="0 0 120 120" style={{ position: "absolute" }}>
        <Circle cx="60" cy="60" r={r} stroke={colors.trackBg} strokeWidth={11} fill="none" />
        <Circle
          cx="60"
          cy="60"
          r={r}
          stroke={colors.accent}
          strokeWidth={11}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${Math.max(filled, 3)} ${c}`}
          transform="rotate(-90 60 60)"
        />
      </Svg>
      <Ltr size={label.length > 7 ? 15 : 24} weight="900">
        {label}
      </Ltr>
    </View>
  );
}

/** A probability: the first percentage as a ring (no dial), and the rest of
 * the calculator's percentages (other time horizons, other outcomes) as a
 * table under it. A result that is a sentence or a label sits under that. */
export function RiskResult({ results }: ResultProps) {
  const shown = useShown();
  const primary = results.find((r) => valueKind(r.answerText) === "pct") ?? results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "");
  const label = p.text.replace(/\s*%\s*$/, "%").replace(/\s+/g, "");
  const rest = results.filter((r) => r.position !== primary.position).map(shown);
  const rows = rest.filter((r) => r.text.length <= 24 && !r.text.includes("\n"));
  const labels = rest.filter((r) => !rows.includes(r) && r.text.length <= 40 && !r.text.includes("\n"));
  const others = rest.filter((r) => !rows.includes(r) && !labels.includes(r));
  const tone = toneOf(`${p.en} ${labels.map((l) => l.en).join(" ")}`);

  return (
    <ResultCard title={p.title} tone={tone === "info" ? "info" : tone}>
      <View style={{ alignItems: "center", gap: 6 }}>
        {value !== null ? <Ring percent={value} label={label} /> : <Ltr size={26} weight="900">{p.text}</Ltr>}
      </View>
      {rows.length ? <Rows rows={rows.map((r) => ({ label: r.title, value: r.text }))} /> : null}
      {labels.map((l, i) => (
        <Chip key={i} text={l.text} tone={toneOf(l.en)} />
      ))}
      <Extras items={others} />
    </ResultCard>
  );
}
