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

export type OutlineNode = {
  id: string;
  title: string;
  depth: number;
};

const TOKEN_RE = /<ul[^>]*>|<\/ul\s*>|<a[^>]*onclick="doOperation\(\{sectionName:&quot;([^"&]+)&quot;\}\)"[^>]*>([\s\S]*?)<\/a>/gi;

const ENTITIES: Record<string, string> = {
  "&nbsp;": " ",
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
};

function stripHtml(fragment: string): string {
  const withoutTags = fragment.replace(/<[^>]+>/g, "");
  return withoutTags
    .replace(/&nbsp;|&amp;|&lt;|&gt;|&quot;|&#39;/g, (m) => ENTITIES[m] ?? m)
    .replace(/\s+/g, " ")
    .trim();
}

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
      const title = stripHtml(rawTitle ?? "");
      if (id && title) {
        // Outline nesting starts one <ul> deep (the outer list itself), so
        // subtract 1 to make the top-level headings depth 0.
        nodes.push({ id, title, depth: Math.max(0, depth - 1) });
      }
    }
  }
  return nodes;
}
