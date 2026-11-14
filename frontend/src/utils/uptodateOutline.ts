/**
 * Parses the `outline_html` UpToDate ships with every article — a nested
 * `<ul>` of `<a onclick="doOperation({sectionName:&quot;H1&quot;})">TITLE</a>`
 * links — into a flat, indented list `{ id, title, depth }[]` the app can
 * render as a native (themed, RTL-aware) list. `id` matches an
 * `id="H1"`-style anchor already present in `body_html`, so tapping an entry
 * can scroll the article straight to that heading.
 *
 * No DOM parser is used (none is reliably available on native RN), just a
 * single regex sweep tracking <ul>/</ul> nesting depth as it goes.
 */

import { numberByDepth } from "@/components/article/numbering";

import { stripHtml } from "./html";

export type OutlineNode = {
  id: string;
  title: string;
  depth: number;
};

const TOKEN_RE = /<ul[^>]*>|<\/ul\s*>|<a[^>]*onclick="doOperation\(\{sectionName:&quot;([^"&]+)&quot;\}\)"[^>]*>([\s\S]*?)<\/a>/gi;

export function parseOutline(outlineHtml: string): OutlineNode[] {
  if (!outlineHtml) return [];
  const nodes: OutlineNode[] = [];
  let depth = 0;
  let match: RegExpExecArray | null;
  TOKEN_RE.lastIndex = 0;
  while ((match = TOKEN_RE.exec(outlineHtml))) {
    const token = match[0];
    if (token[1] === "u") {
      // <ul ...>
      depth += 1;
    } else if (token[1] === "/") {
      // </ul>
      depth = Math.max(0, depth - 1);
    } else {
      const [, id, rawTitle] = match;
      // Some sub-headings are listed as "- Heart failure outcomes" while
      // the heading in the body has no dash.
      const title = stripHtml(rawTitle ?? "").replace(/^[-–—•]\s+/, "");
      if (id && title) {
        // Outline nesting starts one <ul> deep (the outer list itself), so
        // subtract 1 to make the top-level headings depth 0.
        nodes.push({ id, title, depth: Math.max(0, depth - 1) });
      }
    }
  }
  return nodes;
}

export type NumberedOutlineNode = OutlineNode & { num: string | null };

export type OutlineTop = NumberedOutlineNode & { children: NumberedOutlineNode[] };

/** The outline as the article reads: UpToDate repeats "Summary and
 * recommendations" as a shortcut at the very top, so only the last
 * occurrence of each heading id is kept, then every heading is numbered
 * ("3", "3.1", "3.1.2") -- except REFERENCES, which stays unnumbered. */
export function numberedOutline(outlineHtml: string): NumberedOutlineNode[] {
  const nodes = parseOutline(outlineHtml);
  const last = new Map<string, number>();
  nodes.forEach((node, i) => last.set(node.id, i));
  const unique = nodes.filter((node, i) => last.get(node.id) === i);
  return numberByDepth(
    unique,
    (node) => node.depth === 0 && (node.id === "references" || /^references$/i.test(node.title.trim())),
  );
}

/** Top-level headings, each with its direct sub-headings. */
export function outlineTops(nodes: NumberedOutlineNode[]): OutlineTop[] {
  const tops: OutlineTop[] = [];
  for (const node of nodes) {
    if (node.depth === 0) tops.push({ ...node, children: [] });
    else if (node.depth === 1 && tops.length) tops[tops.length - 1].children.push(node);
  }
  return tops;
}

/** A topic's "last updated" date as the cards show it: "Feb 11, 2026" ->
 * "Feb 2026". */
export function shortDate(updated: string): string {
  return updated.replace(/\s+\d{1,2},/, "");
}

// ---- "Related": the outline's graphics, calculators and related topics ----

export type RelatedItem = {
  title: string;
  /** a graphic (table, figure, algorithm...) opens in the viewer; a topic
   * (or calculator) opens its own page */
  target: { graphic: string } | { topic: string };
};

export type RelatedGroup = {
  /** "graphics" | "calculators" | "topics" */
  kind: "graphics" | "calculators" | "topics";
  /** UpToDate's own heading: "Tables", "Figures", "Algorithms"...; "" for
   * calculators and related topics */
  heading: string;
  items: RelatedItem[];
};

const RELATED_SECTIONS: [RelatedGroup["kind"], string][] = [
  ["graphics", "outlineRelatedGraphicsLinks"],
  ["calculators", "outlineRelatedCalculatorsLinks"],
  ["topics", "outlineRelatedTopicsLinks"],
];
const RELATED_TOKEN_RE =
  /<div class="relatedGraphicsHeading"[^>]*>([\s\S]*?)<\/div>|<a\b[^>]*onclick="doOperation\(\{(contentIds?):(?:\[)?&quot;(\d+)&quot;[^"]*\}\)"[^>]*>([\s\S]*?)<\/a>/gi;

/** What an article's outline lists beside its sections: its graphics
 * grouped as UpToDate groups them (Algorithms, Tables, Figures...), its
 * calculators and its related topics. The article body links some of them
 * inline; the outline lists them all. */
export function parseRelated(outlineHtml: string): RelatedGroup[] {
  if (!outlineHtml) return [];
  const groups: RelatedGroup[] = [];
  for (const [kind, id] of RELATED_SECTIONS) {
    const start = outlineHtml.indexOf(`id="${id}"`);
    if (start < 0) continue;
    const end = outlineHtml.indexOf("</section>", start);
    const part = outlineHtml.slice(start, end < 0 ? undefined : end);
    let group: RelatedGroup | null = kind === "graphics" ? null : { kind, heading: "", items: [] };
    if (group) groups.push(group);
    RELATED_TOKEN_RE.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = RELATED_TOKEN_RE.exec(part))) {
      const [, heading, op, contentId, rawTitle] = match;
      if (heading !== undefined) {
        group = { kind, heading: stripHtml(heading), items: [] };
        groups.push(group);
        continue;
      }
      // the legacy "- " before each graphic's title
      const title = stripHtml(rawTitle ?? "").replace(/^[-–—•]\s+/, "");
      if (!title || !contentId) continue;
      if (!group) {
        group = { kind, heading: "", items: [] };
        groups.push(group);
      }
      group.items.push({ title, target: op === "contentIds" ? { graphic: contentId } : { topic: contentId } });
    }
  }
  return groups.filter((g) => g.items.length > 0);
}

export function relatedCount(groups: RelatedGroup[]): number {
  return groups.reduce((sum, g) => sum + g.items.length, 0);
}
