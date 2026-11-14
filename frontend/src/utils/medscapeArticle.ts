/**
 * Turns a Medscape article's section tree into what its home page and
 * reader need: each headed section's number ("3", "3.1", "3.1.2"), the
 * top-level sections with their reading time and sub-headings, and the
 * article's overall counts.
 *
 * Sections are addressed by their index path ("2.0.1") -- stable for a given
 * article, and what the reader uses to find a section's view again.
 */

import { MedscapeBlock, MedscapeSection } from "@/api/types";
import { countWords, numberByDepth, readingMinutes } from "@/components/article/numbering";

export type MedscapeTop = {
  index: number;
  path: string;
  heading: string;
  num: string | null;
  minutes: number;
  children: { path: string; heading: string; num: string | null }[];
};

export type MedscapeModel = {
  /** section path -> its number, for headed sections only */
  numbers: Map<string, string | null>;
  /** every headed section in reading order */
  headed: { path: string; heading: string; depth: number; num: string | null }[];
  tops: MedscapeTop[];
  figures: number;
  minutes: number;
};

// Top-level sections that sum the article up, best first -- the home page
// offers a jump straight to the first one present.
const SUMMARY_HEADINGS = [
  "key takeaways",
  "key points",
  "practice essentials",
  "guidelines summary",
  "summary",
  "latest guidance updates",
  "conclusion",
];

const REFERENCE_HEADINGS = ["references", "reference"];

export function blockText(block: MedscapeBlock): string {
  switch (block.type) {
    case "paragraph":
      return block.text;
    case "list":
      return block.items.join(" ");
    case "table":
      return [...(block.headers ?? []), ...block.rows.flat()].join(" ");
    default:
      return "";
  }
}

function sectionWords(section: MedscapeSection): number {
  let words = countWords(section.heading);
  for (const block of section.blocks) words += countWords(blockText(block));
  for (const child of section.children) words += sectionWords(child);
  return words;
}

function sectionFigures(section: MedscapeSection): number {
  let figures = section.blocks.filter((b) => b.type === "image" || b.type === "table").length;
  for (const child of section.children) figures += sectionFigures(child);
  return figures;
}

export function buildMedscapeModel(sections: MedscapeSection[]): MedscapeModel {
  const flat: { path: string; heading: string; depth: number }[] = [];
  const walk = (list: MedscapeSection[], depth: number, prefix: string) => {
    list.forEach((section, i) => {
      const path = prefix ? `${prefix}.${i}` : String(i);
      if (section.heading) flat.push({ path, heading: section.heading, depth });
      walk(section.children, depth + 1, path);
    });
  };
  walk(sections, 0, "");

  const headed = numberByDepth(flat, (s) => s.depth === 0 && REFERENCE_HEADINGS.includes(s.heading.trim().toLowerCase()));
  const numbers = new Map(headed.map((s) => [s.path, s.num] as const));

  let totalWords = 0;
  let figures = 0;
  const tops: MedscapeTop[] = [];
  sections.forEach((section, index) => {
    const words = sectionWords(section);
    totalWords += words;
    figures += sectionFigures(section);
    if (!section.heading) return;
    const path = String(index);
    tops.push({
      index,
      path,
      heading: section.heading,
      num: numbers.get(path) ?? null,
      minutes: readingMinutes(words),
      children: section.children
        .map((child, i) => ({ path: `${path}.${i}`, heading: child.heading }))
        .filter((child) => !!child.heading)
        .map((child) => ({ ...child, num: numbers.get(child.path) ?? null })),
    });
  });

  return { numbers, headed, tops, figures, minutes: readingMinutes(totalWords) };
}

export function summaryTop(model: MedscapeModel): MedscapeTop | null {
  for (const wanted of SUMMARY_HEADINGS) {
    const top = model.tops.find((t) => t.heading.trim().toLowerCase() === wanted);
    if (top && top !== model.tops[0]) return top;
  }
  return null;
}

export function referencesTop(model: MedscapeModel): MedscapeTop | null {
  return model.tops.find((t) => REFERENCE_HEADINGS.includes(t.heading.trim().toLowerCase())) ?? null;
}

/** Two-digit table-of-contents label: "01", "02" ... "12". */
export function tocLabel(num: string | null): string {
  if (!num) return "";
  return num.length === 1 ? `0${num}` : num;
}
