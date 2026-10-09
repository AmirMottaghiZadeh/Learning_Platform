const NAMED_ENTITIES: Record<string, string> = {
  nbsp: " ",
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
  ge: "≥",
  GreaterEqual: "≥",
  le: "≤",
  ne: "≠",
  plusmn: "±",
  deg: "°",
  times: "×",
  divide: "÷",
  percnt: "%",
  copy: "©",
  micro: "µ",
  alpha: "α",
  beta: "β",
  Beta: "Β",
  gamma: "γ",
  delta: "δ",
  mu: "μ",
  ndash: "–",
  mdash: "—",
  hellip: "…",
  rsquo: "’",
  lsquo: "‘",
  rdquo: "”",
  ldquo: "“",
  eacute: "é",
  oacute: "ó",
  ntilde: "ñ",
  Ouml: "Ö",
};

/** Named (`&ge;`), decimal (`&#39;`) and hex (`&#x2265;`) HTML entities --
 * medical calculator/reference text leans heavily on comparison symbols
 * (&ge;, &le;) and Greek letters that a narrow hardcoded set would miss. */
function decodeEntities(text: string): string {
  return text.replace(/&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z]+);/g, (match, body: string) => {
    if (body[0] === "#") {
      const isHex = body[1] === "x" || body[1] === "X";
      const code = isHex ? parseInt(body.slice(2), 16) : parseInt(body.slice(1), 10);
      return Number.isNaN(code) ? match : String.fromCodePoint(code);
    }
    return NAMED_ENTITIES[body] ?? match;
  });
}

/** Strips a fragment of inline HTML down to one line of plain text --
 * for short strings (titles, labels) where structure doesn't matter. */
export function stripHtml(fragment: string): string {
  return decodeEntities(fragment.replace(/<[^>]+>/g, "")).replace(/\s+/g, " ").trim();
}

/** Like `stripHtml`, but keeps paragraph/list-item breaks as newlines --
 * for longer HTML content (a few paragraphs of clinical text) where that
 * structure still helps readability once rendered as plain text. */
export function htmlToParagraphs(html: string): string {
  if (!html) return "";
  const withBreaks = html.replace(/<\/(p|li|div)>|<br\s*\/?>/gi, "\n");
  return decodeEntities(withBreaks.replace(/<[^>]+>/g, ""))
    .split("\n")
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
}

export type AboutBlock =
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; label: string | null; text: string }
  | { kind: "listItem"; label: string | null; text: string };

// A label is short and word-based, immediately followed by its content --
// matches the same "Score 0 or 1: Patient is less likely to require..." /
// "Age: ≥60 years: 1 point" shape seen across the imported calculator
// "about" HTML (confirmed against the real dataset: ~26% of entries use
// <ul><li> criteria lists, many with this exact label-then-value form).
const LABEL_RE = /^([^:：]{1,40}):\s*(.+)$/s;

function splitLabel(text: string): { label: string | null; text: string } {
  const m = text.match(LABEL_RE);
  return m ? { label: m[1].trim(), text: m[2].trim() } : { label: null, text };
}

const LIST_PLACEHOLDER = "\u0000LIST";

/** Breaks a calculator's "about" HTML into headings / paragraphs / list
 * items instead of the flat line-per-tag text `htmlToParagraphs` gives --
 * built for "what does this score mean" content specifically, which in the
 * real source data is routinely a <ul> of scoring criteria and/or a run of
 * "<strong>Label</strong>" sub-headings and "Score X:<br>meaning"
 * paragraphs, none of which read as a list or a label once flattened to
 * plain lines. A <br> inside one paragraph is treated as part of that same
 * paragraph (joined with a space, then label-split), not a new block --
 * the "Score 0 or 1:<br>Patient is less likely..." case this is for is one
 * thought split across a line break, not two. */
export function parseAboutHtml(html: string): AboutBlock[] {
  if (!html) return [];

  // Pull every <ul>/<ol> out first (regardless of whether it's nested
  // inside a <p>, which the real data does) so the <p> splitter below never
  // has to reason about a list sitting inside a paragraph.
  const lists: string[][] = [];
  const withPlaceholders = html.replace(
    /<(ul|ol)[^>]*>([\s\S]*?)<\/\1>/gi,
    (_match, _tag: string, inner: string) => {
      const items: string[] = [];
      const liRe = /<li[^>]*>([\s\S]*?)<\/li>/gi;
      let liMatch: RegExpExecArray | null;
      while ((liMatch = liRe.exec(inner))) items.push(liMatch[1]);
      const index = lists.length;
      lists.push(items);
      return `${LIST_PLACEHOLDER}${index}\u0000`;
    },
  );

  // Split on <p>/</p> as boundary markers rather than extracting only their
  // contents -- the real data routinely puts a <ul> as a *sibling* of <p>
  // tags, not nested inside one (confirmed: 38/40 real list-containing
  // calculators sampled), and treating <p> as a wrapper to extract from
  // (not just a separator) silently dropped that sibling content entirely.
  const chunks = withPlaceholders
    .split(/<\/?p[^>]*>/gi)
    .map((c) => c.trim())
    .filter(Boolean);

  const blocks: AboutBlock[] = [];
  const placeholderRe = new RegExp(`(${LIST_PLACEHOLDER}\\d+\u0000)`, "g");

  for (const chunk of chunks) {
    for (const segment of chunk.split(placeholderRe)) {
      if (!segment) continue;
      const placeholderMatch = segment.match(new RegExp(`^${LIST_PLACEHOLDER}(\\d+)\u0000$`));
      if (placeholderMatch) {
        for (const raw of lists[Number(placeholderMatch[1])] ?? []) {
          const text = stripHtml(raw);
          if (!text) continue;
          const { label, text: body } = splitLabel(text);
          blocks.push({ kind: "listItem", label, text: body });
        }
        continue;
      }

      const isHeading = /^\s*<(strong|b)>[\s\S]*<\/\1>\s*$/i.test(segment);
      const joined = segment.replace(/<br\s*\/?>/gi, " ");
      const text = stripHtml(joined);
      if (!text) continue;
      if (isHeading) {
        blocks.push({ kind: "heading", text });
      } else {
        const { label, text: body } = splitLabel(text);
        blocks.push({ kind: "paragraph", label, text: body });
      }
    }
  }
  return blocks;
}
