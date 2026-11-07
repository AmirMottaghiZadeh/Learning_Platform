import { apiClient } from "./client";

export type SupportConversation = {
  id: string; subject: string; kind: "general" | "topic"; status: "open" | "closed";
  unread: number; user_read_id: number; staff_read_id: number; updated_at: string;
};
export type SupportMessage = { id: number; client_id: string; text: string; from_staff: boolean; created_at: string };
export type SupportMessages = { messages: SupportMessage[]; has_older: boolean; user_read_id: number; staff_read_id: number };
export type SupportSummary = { unread: number; web_push_public_key: string; web_push_configured: boolean };
export type SupportSubscription = { device_id: string; platform: "android" | "web"; enabled: boolean; expo_token?: string; web_subscription?: unknown };

export const supportApi = {
  conversations: () => apiClient.get<SupportConversation[]>("/support/conversations/").then(r => r.data),
  create: (subject?: string) => apiClient.post<SupportConversation>("/support/conversations/", { subject }).then(r => r.data),
  messages: (id: string, params?: { after?: number; before?: number }) => apiClient.get<SupportMessages>(`/support/conversations/${id}/messages/`, { params }).then(r => r.data),
  send: (id: string, text: string, client_id: string) => apiClient.post<SupportMessage>(`/support/conversations/${id}/messages/`, { text, client_id }).then(r => r.data),
  read: (id: string, through: number) => apiClient.post(`/support/conversations/${id}/read/`, { through }),
  summary: () => apiClient.get<SupportSummary>("/support/summary/").then(r => r.data),
  subscribe: (body: SupportSubscription) => apiClient.post("/support/subscription/", body).then(r => r.data),
};
