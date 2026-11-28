import { apiClient } from "./client";
import type { MediaContent } from "@/components/article/mediaPage";

export type ReferenceMedia = { key: string; kind: "table" | "image"; title: string; caption: string;
  article_id: string; content_hash: string; graphic_hash?: string; content_complete?: boolean;
  asset_id?: string; is_algorithm?: boolean };

export function referenceMediaId(item: ReferenceMedia) {
  return item.asset_id || (item.key.startsWith("graphic-") ? item.key : `${item.article_id}:${item.key}`);
}

export const referenceMediaApi = {
  get: (item: ReferenceMedia) => apiClient.get<MediaContent>(`/uptodate/topics/${encodeURIComponent(item.article_id)}/media/${encodeURIComponent(item.key)}/`,
    {params:{content_hash:item.content_hash,graphic_hash:item.graphic_hash}}).then(r => r.data),
};
