import React, { useMemo } from "react";
import { AppText } from "@/components/primitives/AppText";
import { answerSegments } from "@/utils/referenceAnswer";

export function ReferenceAnswerText({ text, testID }: { text: string; testID?: string }) {
  const segments = useMemo(() => answerSegments(text), [text]);
  return <AppText testID={testID} selectable size={14}>
    {segments.map((segment, index) => segment.bold
      ? <AppText key={index} weight="700" size={14}>{segment.text}</AppText>
      : segment.text)}
  </AppText>;
}
