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
