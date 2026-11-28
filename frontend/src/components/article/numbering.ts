/**
 * Section numbers for the articles' three heading levels ("3", "3.1",
 * "3.1.2"), shared by UpToDate (numbered from its outline) and the Medscape
 * guideline/disease articles (numbered from their section tree), so the
 * article's table of contents and its headings always show the same number.
 */

export type Numbered<T> = T & { num: string | null };

/** Numbers a flat, depth-tagged list in reading order. `skip` leaves an
 * entry unnumbered (e.g. REFERENCES) without disturbing its siblings. A jump
 * of more than one level counts the missing parent as 1. */
export function numberByDepth<T extends { depth: number }>(
  nodes: T[],
  skip?: (node: T) => boolean,
): Numbered<T>[] {
  const counters: number[] = [];
  return nodes.map((node) => {
    if (skip?.(node)) return { ...node, num: null };
    const depth = Math.max(0, node.depth);
    while (counters.length < depth) counters.push(1);
    counters.length = depth + 1;
    counters[depth] = (counters[depth] ?? 0) + 1;
    return { ...node, num: counters.join(".") };
  });
}

/** Rough reading time, ~220 words a minute, never below one minute. */
export function readingMinutes(wordCount: number): number {
  return Math.max(1, Math.round(wordCount / 220));
}

export function countWords(text: string): number {
  const matches = text.match(/\S+/g);
  return matches ? matches.length : 0;
}
