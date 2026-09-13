const ENTITIES: Record<string, string> = {
  "&nbsp;": " ",
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
};

function decodeEntities(text: string): string {
  return text.replace(/&nbsp;|&amp;|&lt;|&gt;|&quot;|&#39;/g, (m) => ENTITIES[m] ?? m);
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
