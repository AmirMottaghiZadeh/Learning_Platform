import { decodeEntities, stripHtml } from "./html";

export type ReferenceContentLink = { id: string; title: string };
export type ReferenceContent =
  | { kind: "article" }
  | { kind: "calculator" }
  | { kind: "directory"; links: ReferenceContentLink[]; introduction: string };

function attribute(tag: string, name: string): string {
  const opening = tag.slice(0, tag.indexOf(">") + 1);
  const match = opening.match(new RegExp(`(?:^|\\s)${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, "i"));
  return decodeEntities(match?.[1] ?? match?.[2] ?? match?.[3] ?? "");
}

/** Scope to the content body, excluding title, copyright and related-topic rails. */
function topicBody(html: string): string | null {
  const tags = /<\/?div\b[^>]*>/gi;
  let start = -1;
  let depth = 0;
  let token: RegExpExecArray | null;
  while ((token = tags.exec(html))) {
    if (start < 0) {
      if (attribute(token[0], "id") === "topicText" && !token[0].startsWith("</")) { start = tags.lastIndex; depth = 1; }
    } else {
      depth += token[0].startsWith("</") ? -1 : 1;
      if (!depth) return html.slice(start, token.index);
    }
  }
  return null;
}

/** Conservative classification works for downloaded snapshots as well as online data.
 * FTS/JSON type=1 also includes calculators and redirect lists; it cannot decide this. */
export function classifyReferenceContent(topic: { title: string; body_html: string }): ReferenceContent {
  if (/^\s*Calculator\s*:/i.test(topic.title) && /<form\b/i.test(topic.body_html)) return { kind: "calculator" };
  const body = topicBody(topic.body_html);
  if (!body || /<(?:form|script|iframe|table|img)\b/i.test(body)) return { kind: "article" };
  const links: ReferenceContentLink[] = [];
  let invalidLink = false;
  const remainder = body.replace(/<a\b[^>]*>[\s\S]*?<\/a\s*>/gi, (tag) => {
    const operation = attribute(tag, "onclick");
    const id = attribute(tag, "data-topicid") || operation.match(/\bcontentId\s*:\s*["']?(\d+)["']?\s*[,}]/)?.[1] || "";
    const title = stripHtml(tag);
    if (!/^\d+$/.test(id) || !title) invalidLink = true;
    else if (!links.some(link => link.id === id)) links.push({ id, title });
    return "";
  });
  const introduction = stripHtml(remainder);
  // Only link-only lists or the source's explicit split-monograph notice qualify.
  // A short article with two references is still an article.
  const splitNotice = /^Information for this drug is presented separately based upon the following [\w\s]+:$/i.test(introduction);
  if (invalidLink || links.length < 2 || links.length > 100 || !/<(?:ul|ol)\b/i.test(body) || (introduction && !splitNotice)) return { kind: "article" };
  return { kind: "directory", links, introduction };
}
