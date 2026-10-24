import React from "react";

import { ResultCard, ResultProps, RichLines, toneOf, useShown } from "./common";

/** The fallback: each result as a titled card of text. */
export function PlainResult({ results }: ResultProps) {
  const shown = useShown();
  return (
    <>
      {results.map((r) => {
        const s = shown(r);
        return (
          <ResultCard key={r.position} title={s.title} tone={toneOf(s.en)}>
            <RichLines text={s.text} />
          </ResultCard>
        );
      })}
    </>
  );
}
