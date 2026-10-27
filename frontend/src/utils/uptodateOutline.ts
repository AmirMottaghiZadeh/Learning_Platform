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
