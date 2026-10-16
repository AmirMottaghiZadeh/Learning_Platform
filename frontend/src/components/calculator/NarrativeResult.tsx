import React from "react";
import { View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";

import { Collapse, ResultCard, ResultProps, RichLines, toneOf, useDisplayText, useShown } from "./common";

/** Text guidance. Short answers get a headline and the explanation under it;
 * long, multi-part ones become folding sections, the first one open. */
export function NarrativeResult({ results, info }: ResultProps) {
  const { isFa } = useLang();
  const shown = useShown();
  const display = useDisplayText();
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
        return (
          <ResultCard key={i} title={it.title} tone={toneOf(it.en)}>
            <AppText weight="900" size={18} style={{ lineHeight: 29, writingDirection: isFa ? "rtl" : "ltr" }}>
              {display(head)}
            </AppText>
            {body ? <RichLines text={body} /> : <View />}
          </ResultCard>
        );
      })}
    </>
  );
}
