import React from "react";
import { View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { polarity, resultText, valueKind } from "@/utils/calculatorModel";

import {
  Chip,
  Collapse,
  Explain,
  Hero,
  ResultCard,
  ResultProps,
  RichLines,
  Tone,
  tiersTones,
  toneOf,
  useDisplayText,
  useShown,
  useToneStyle,
} from "./common";

function Badge({ kind, color, bg }: { kind: "ok" | "alert" | "neutral"; color: string; bg: string }) {
  return (
    <Svg width={52} height={52} viewBox="0 0 48 48">
      <Circle cx="24" cy="24" r="22" fill={bg} stroke={color} strokeWidth={2} />
      {kind === "ok" ? (
        <Path d="M14 25l7 7 14-15" fill="none" stroke={color} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round" />
      ) : kind === "alert" ? (
        <Path d="M16 16l16 16M32 16L16 32" fill="none" stroke={color} strokeWidth={4.5} strokeLinecap="round" />
      ) : (
        <Path d="M24 15v2M24 22v11" fill="none" stroke={color} strokeWidth={4.5} strokeLinecap="round" />
      )}
    </Svg>
  );
}

/** A verdict, centred in the colour of how serious it is: a yes/no badge, a
 * position on a ladder of categories, or a decision with the action to take.
 * What explains it sits below. */
export function VerdictResult({ results, info }: ResultProps) {
  const { colors } = useTheme();
  const { isFa, row, t } = useLang();
  const shown = useShown();
  const display = useDisplayText();
  const toneStyle = useToneStyle();

  const main = results.find((r) => ["label", "mixed", "text"].includes(valueKind(r.answerText))) ?? results[0];
  const m = shown(main);
  const rest = results.filter((r) => r.position !== main.position).map(shown).filter((r) => r.text);
  const pol = polarity(m.en);
  // What the words say, else whether it is good or bad news.
  const tone: Tone = toneOf(m.en) !== "info" ? toneOf(m.en) : pol === "ok" ? "ok" : pol === "alert" ? "warn" : "info";

  if (info.verdict === "ladder" && info.ladder) {
    const at = info.ladder.findIndex((r) => r.en === m.en);
    const tones = tiersTones(info.ladder.map((r) => r.en));
    const headTone = at >= 0 ? tones[at] : tone;
    return (
      <ResultCard title={m.title} tone={headTone} center>
        <Hero label={m.text} tone={headTone} />
        <View style={{ gap: 4 }}>
          {info.ladder.map((rung, i) => {
            const active = i === at;
            const rt = toneStyle(tones[i]);
            return (
              <View
                key={i}
                style={{
                  flexDirection: row,
                  alignItems: "center",
                  gap: 8,
                  paddingHorizontal: 10,
                  paddingVertical: 7,
                  borderRadius: 10,
                  borderWidth: 1,
                  borderColor: active ? rt.border : "transparent",
                  backgroundColor: active ? rt.bg : "transparent",
                }}
              >
                <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: active ? rt.label : `${rt.label}55` }} />
                <AppText weight={active ? "800" : "600"} size={12.5} color={active ? rt.label : colors.muted} style={{ flex: 1, writingDirection: isFa ? "rtl" : "ltr" }}>
                  {display((isFa ? rung.fa : rung.en) || rung.en)}
                </AppText>
              </View>
            );
          })}
        </View>
        <Explain items={rest} />
      </ResultCard>
    );
  }

  if (info.verdict === "decision") {
    return (
      <ResultCard title={m.title} tone={tone} center>
        <View style={{ alignItems: "center", gap: 8 }}>
          <Chip text={t("calcAction")} tone={tone === "info" ? "ok" : tone} />
          <Hero label={m.text} tone={tone === "info" ? "ok" : tone} />
        </View>
        {rest.length ? (
          <Collapse title={t("calcWhy")}>
            {rest.map((r, i) => (
              <View key={i} style={{ gap: 2 }}>
                <AppText weight="800" size={12}>
                  {r.title}
                </AppText>
                <RichLines text={r.text} />
              </View>
            ))}
          </Collapse>
        ) : null}
      </ResultCard>
    );
  }

  const ts = toneStyle(tone);
  return (
    <ResultCard title={m.title} tone={tone} center>
      <View style={{ alignItems: "center", gap: 10 }}>
        <Badge kind={pol} color={ts.label} bg={ts.bg === "transparent" ? colors.softBg : ts.bg} />
        <Hero label={resultText(m.text)} tone={tone} />
      </View>
      <Explain items={rest} />
    </ResultCard>
  );
}
