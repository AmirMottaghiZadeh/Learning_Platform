import React, { useMemo } from "react";
import { AppText } from "@/components/primitives/AppText";
import { hasPersianLetters } from "@/utils/bidi";
import { answerSegments } from "@/utils/referenceAnswer";

export function ReferenceAnswerText({ text, testID }: { text: string; testID?: string }) {
  const segments = useMemo(() => answerSegments(text), [text]);
  const direction = hasPersianLetters(text) ? "rtl" : "ltr";
  return <AppText testID={testID} selectable size={15} style={{ writingDirection: direction, textAlign: direction === "rtl" ? "right" : "left" }}>
    {segments.map((segment, index) => segment.bold
      ? <AppText key={index} weight="700" size={15} style={{ writingDirection: direction }}>{segment.text}</AppText>
      : segment.text)}
  </AppText>;
}
