import { apiClient } from "./client";

export type SearchCreditPackage = { id: number; name: string; credits: string; price_toman: number };
export type SearchWallet = {
  balance: string; available: string; exhausted: boolean;
  billing_enabled: boolean; pricing_ready: boolean; can_search: boolean;
  topups_enabled: boolean; packages: SearchCreditPackage[]; gateways: { kind: string; name: string }[];
  usage_30_days: { credits: string };
  completed_topups?: string[];
};
export type SearchCreditHistory = {
  transactions: { id: string; kind: string; label: string; amount: string; balance_after: string;
    note: string; created_at: string; usage_pending?: boolean }[];
  pending: { id: string; status: string; usage_pending: boolean; created_at: string }[];
  next_offset: number | null;
};

export const searchWalletApi = {
  summary: () => apiClient.get<SearchWallet>("/ai-lab/wallet/").then(r => r.data),
  history: (offset = 0) => apiClient.get<SearchCreditHistory>("/ai-lab/wallet/history/", { params: { offset } }).then(r => r.data),
  topup: (body: { package_id: number; request_id: string; gateway?: string; client: "web" | "android"; expected_price_toman?: number }) =>
    apiClient.post<{ order_id: number; status: string; payment_url: string }>("/ai-lab/wallet/topups/", body).then(r => r.data),
};
