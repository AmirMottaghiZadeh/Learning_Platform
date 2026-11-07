import { medscapeApi } from "@/api/endpoints";
import { queryClient } from "@/api/queryClient";
import type { MedscapeArticleDetail, MedscapeBlock, MedscapeSection, UptodateArticle } from "@/api/types";

export const escapeReaderText = (text: string) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");

/** Convert the structured reference into the same reading document used by
 * UpToDate. Text is escaped; no upstream string becomes executable markup. */
export function medscapeDocument(article: MedscapeArticleDetail, images: Map<number, string> = new Map()): UptodateArticle {
  const e = escapeReaderText;
  const blockHtml = (block: MedscapeBlock): string => {
    if (block.type === "paragraph") return `<p>${e(block.text)}</p>`;
    if (block.type === "list") {
      const tag = block.ordered ? "ol" : "ul";
      return `<${tag}>${block.items.map((item) => `<li>${e(item)}</li>`).join("")}</${tag}>`;
    }
    if (block.type === "table") return `<table>${block.headers ? `<thead><tr>${block.headers.map((cell) => `<th>${e(cell)}</th>`).join("")}</tr></thead>` : ""}<tbody>${block.rows.map((row) => `<tr>${row.map((cell) => `<td>${e(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    const src = images.get(block.id);
    return `<figure>${src ? `<button type="button" data-reader-image="${block.id}" aria-label="${e(block.alt || "Open image")}" style="border:0;background:transparent;padding:0;width:100%;cursor:zoom-in"><img src="${e(src)}" alt="${e(block.alt)}" style="max-width:100%;height:auto"></button>` : `<p>${e(block.alt || "Image unavailable")}</p>`}${block.caption ? `<figcaption>${e(block.caption)}</figcaption>` : ""}</figure>`;
  };
  const walk = (sections: MedscapeSection[], prefix = "", depth = 0): { html: string; outline: string } => {
    let html = "", outline = "<ul>";
    sections.forEach((section, index) => {
      const path = prefix ? `${prefix}.${index}` : String(index);
      const id = `med-${path}`;
      const children = walk(section.children, path, depth + 1);
      const tag = `h${Math.min(depth + 1, 6)}`;
      html += `<section id="${id}">${section.heading ? `<${tag}>${e(section.heading)}</${tag}>` : ""}${section.blocks.map(blockHtml).join("")}${children.html}</section>`;
      // Headless sections still carry their index path for jump navigation.
      outline += `<li>${section.heading ? `<a onclick="doOperation({sectionName:&quot;${id}&quot;})">${e(section.heading)}</a>` : ""}${section.children.length ? children.outline : ""}</li>`;
    });
    return { html, outline: outline + "</ul>" };
  };
  const document = walk(article.sections);
  return { id: article.slug, title: article.title, reference_kind: article.kind, section: article.categories.map((c) => c.specialty).join(" · "), version: "", updated: article.latest_update || "", contributors: [], outline_html: document.outline, body_html: `<div id="topicText">${article.meta ? `<p class="reader-meta">${e(article.meta)}</p>` : ""}${document.html}</div>` };
}

export async function loadMedscapeReader(slug: string): Promise<UptodateArticle> {
  const article = await queryClient.fetchQuery({ queryKey: ["medscape-article", slug], queryFn: () => medscapeApi.detail(slug) });
  const ids = new Set<number>();
  const collect = (sections: MedscapeSection[]) => {
    for (const section of sections) {
      for (const block of section.blocks) if (block.type === "image") ids.add(block.id);
      collect(section.children);
    }
  };
  collect(article.sections);
  const images = new Map<number, string>();
  const pending = [...ids];
  // Bound image concurrency so a long article doesn't exhaust native sockets.
  await Promise.all(Array.from({ length: Math.min(4, pending.length) }, async () => {
    while (pending.length) {
      const id = pending.shift()!;
      try {
        const image = await queryClient.fetchQuery({ queryKey: ["medscape-image", id], queryFn: () => medscapeApi.image(id) });
        if (/^image\/(?:png|jpeg|gif|webp|avif)$/i.test(image.content_type)) images.set(id, `data:${image.content_type};base64,${image.data_base64}`);
      } catch { /* Keep the caption/alternative text readable. */ }
    }
  }));
  return medscapeDocument(article, images);
}
