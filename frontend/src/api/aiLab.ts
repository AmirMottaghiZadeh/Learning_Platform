import { apiClient } from "./client";

export type LabModel = "luna";
export const LAB_MODEL: LabModel = "luna";
export type LabSource = "uptodate";
export type LabStatus = { enabled: boolean; models: Record<LabModel, string>; sources: Record<LabSource, string> };
export type LabCitation = {
  source_id: string; source: LabSource; title: string; section: string;
  quote: string; summary_fa: string; content_hash: string;
  target: { screen: string; params: Record<string, unknown> };
};
export type LabResult = {
  model: LabModel; pipeline: string; elapsed_ms: number;
  parts: { question_fa: string; queries: string[]; status: string; clarification_fa: string; items: LabCitation[];
    overview_fa?: string; retrieval?: { selected_passages?: number; reviewed_passages?: number; selected_articles?: number;
      reviewed_articles?: number; early_stopped?: boolean; stop_reason?: string; limited?: boolean } }[];
  warnings: { source: string; code: string }[];
  stages: { stage: string; model: string; latency_ms: number; usage: Record<string, number> }[];
};
export type LabJob = {
  status: "running" | "complete" | "failed"; stage?: string; result?: LabResult;
  revision?: number; findings?: LabFinding[]; findings_limited?: boolean; first_result_ms?: number;
  workflow?: LabWorkflowPart[]; stages_seen?: string[];
  error?: { code: string; provider_status?: number; model?: string };
};
export type LabWorkflowArticle = { id: string; title: string; phase: string;
  sections?: { id: string; heading: string }[]; paragraph_count?: number;
  reviewed_passages: number; reviewing_count: number };
export type LabWorkflowPart = { part_index: number; question_fa: string; queries: string[];
  titles: { id: string; title: string; related_to?: string }[]; articles: LabWorkflowArticle[]; current_article_id?: string };
export type LabFinding = { id: string; sequence: number; part_index: number; question_fa: string;
  article_id: string; published_at: number; citation: LabCitation };
export type ActiveLabJob = LabJob & { job_id: string; question: string; model: LabModel; sources: LabSource[]; status: "running"; stage: string };

export const aiLabApi = {
  active: async (): Promise<ActiveLabJob | null> => (await apiClient.get("/ai-lab/active/")).data.active_job,
  status: async (): Promise<LabStatus> => (await apiClient.get("/ai-lab/status/")).data,
  ask: async (question: string, history: string[]): Promise<{ job_id: string }> =>
    (await apiClient.post("/ai-lab/ask/", { question, model: LAB_MODEL, sources: ["uptodate"], history })).data,
  result: async (id: string, revision?: number): Promise<LabJob> =>
    (await apiClient.get(`/ai-lab/results/${id}/`, { params: revision === undefined ? undefined : { after_revision: revision } })).data,
};
