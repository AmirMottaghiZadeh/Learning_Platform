import { apiClient } from "./client";
import type { MediaContent } from "@/components/article/mediaPage";

export type ReferenceMedia = { key: string; kind: "table" | "image"; title: string; caption: string;
  article_id: string; content_hash: string; graphic_hash?: string; content_complete?: boolean };

export const referenceMediaApi = {
  get: (item: ReferenceMedia) => apiClient.get<MediaContent>(`/uptodate/topics/${encodeURIComponent(item.article_id)}/media/${encodeURIComponent(item.key)}/`,
    {params:{content_hash:item.content_hash,graphic_hash:item.graphic_hash}}).then(r => r.data),
};
