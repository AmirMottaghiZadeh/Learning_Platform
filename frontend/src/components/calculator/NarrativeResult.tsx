import React from "react";
import { View } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";

import { Collapse, Hero, ResultCard, ResultProps, RichLines, toneOf, useShown } from "./common";

/** Text guidance. Short answers get a headline and the explanation under it;
 * long, multi-part ones become folding sections, the first one open. */
export function NarrativeResult({ results, info }: ResultProps) {
  const { colors } = useTheme();
  const shown = useShown();
  const items = results.map(shown).filter((r) => r.text);

  if (info.narrative === "sections") {
    return (
      <ResultCard>
        {items.map((it, i) => (
          <Collapse key={i} title={it.title || "—"} defaultOpen={i === 0}>
            <RichLines text={it.text} />
          </Collapse>
        ))}
      </ResultCard>
    );
  }

  return (
    <>
      {items.map((it, i) => {
        const split = /^(.+?[.!؟])\s+([\s\S]*)$/.exec(it.text) ?? /^(.+?)\n([\s\S]*)$/.exec(it.text);
        const head = split ? split[1].trim() : it.text;
        const body = split ? split[2].trim() : "";
        const tone = toneOf(it.en);
        return (
          <ResultCard key={i} title={it.title} tone={tone} center>
            <Hero label={head} tone={tone} />
            {body ? (
              <View style={{ gap: 10, marginTop: 4 }}>
                <View style={{ height: 1, backgroundColor: colors.border }} />
                <RichLines text={body} />
              </View>
            ) : null}
          </ResultCard>
        );
      })}
    </>
  );
}
