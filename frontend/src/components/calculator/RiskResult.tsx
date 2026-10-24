import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { useTheme } from "@/theme/ThemeProvider";
import { extractNumericValue } from "@/utils/calculatorEngine";
import { valueKind } from "@/utils/calculatorModel";

import { Explain, Hero, Ltr, ResultCard, ResultProps, toneOf, useShown, useToneStyle } from "./common";

function Ring({ percent, label, color }: { percent: number; label: string; color: string }) {
  const { colors } = useTheme();
  const size = 140;
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
          stroke={color}
          strokeWidth={11}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${Math.max(filled, 3)} ${c}`}
          transform="rotate(-90 60 60)"
        />
      </Svg>
      <Ltr size={label.length > 7 ? 15 : 26} weight="900">
        {label}
      </Ltr>
    </View>
  );
}

/** A probability: the first percentage as a ring, centred, in the colour of
 * how serious the calculator calls it when it says so in words; the rest of
 * its percentages (other time horizons, other outcomes) and any explanation
 * below. */
export function RiskResult({ results }: ResultProps) {
  const shown = useShown();
  const { colors } = useTheme();
  const toneStyle = useToneStyle();
  const primary = results.find((r) => valueKind(r.answerText) === "pct") ?? results.find((r) => valueKind(r.answerText) === "num") ?? results[0];
  const p = shown(primary);
  const value = extractNumericValue(primary.answerText ?? "");
  const label = p.text.replace(/\s*%\s*$/, "%").replace(/\s+/g, "");
  const rest = results.filter((r) => r.position !== primary.position).map(shown).filter((r) => r.text);
  // A short wording of the risk ("Low risk") is the verdict; the rest explains.
  const verdict = rest.find((r) => r.text.length <= 40 && !r.text.includes("\n") && valueKind(r.en) === "label");
  const explain = rest.filter((r) => r !== verdict);
  const tone = toneOf(`${p.en} ${verdict?.en ?? ""}`);
  const ringColor = tone === "info" ? colors.accent : toneStyle(tone).label;

  return (
    <ResultCard title={p.title} tone={tone} center>
      <View style={{ alignItems: "center", gap: 6 }}>
        {value !== null ? <Ring percent={value} label={label} color={ringColor} /> : <Hero value={p.text} />}
      </View>
      {verdict ? <Hero label={verdict.text} tone={tone} /> : null}
      <Explain items={explain} />
    </ResultCard>
  );
}
