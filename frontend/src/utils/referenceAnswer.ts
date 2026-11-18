export type AnswerSegment = { text: string; bold: boolean };

/** Render emphasis as text nodes, never as HTML, including an unfinished stream. */
export function answerSegments(value: string): AnswerSegment[] {
  const result: AnswerSegment[] = [];
  let text = "";
  let bold = false;
  const flush = () => { if (text) result.push({ text, bold }); text = ""; };
  for (let i = 0; i < value.length; i++) {
    if (value[i] === "\\" && (value[i + 1] === "*" || value[i + 1] === "\\")) {
      text += value[++i];
    } else if (value.slice(i, i + 2) === "**") {
      flush();
      bold = !bold;
      i++;
    } else {
      text += value[i];
    }
  }
  flush();
  return result;
}

/** Follow the answer's growing tail, independently of source cards below it. */
export function answerFollowOffset(top: number, height: number, viewport: number): number {
  return Math.max(0, top - 12, top + height - Math.max(1, viewport) + 20);
}
