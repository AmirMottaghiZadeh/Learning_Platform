import { apiClient, authenticatedStream } from "./client";
import type { ReferenceMedia } from "./referenceMedia";

export type LabModel = "luna";
export const LAB_MODEL: LabModel = "luna";
export type LabSource = "uptodate";
export type LabStatus = { enabled: boolean; models: Record<LabModel, string>; sources: Record<LabSource, string> };
export type LabCitation = {
  source_id: string; source: LabSource; title: string; section: string;
  quote: string; summary_fa: string; content_hash: string;
  verification?: "retrieved" | "verified";
  context?: { quote: string; source_anchor: string; ordinal: number }[];
  media?: ReferenceMedia[];
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
  feedback_available?: boolean; revision?: number; findings?: LabFinding[]; findings_limited?: boolean; first_result_ms?: number;
  workflow?: LabWorkflowPart[]; stages_seen?: string[];
  answer_drafts?: Record<string, string>;
  cancellable?: boolean;
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

export type LabEvent = { sequence: number } & (
  { type: "snapshot" | "complete"; job: LabJob }
  | { type: "sources"; findings: LabFinding[] }
  | { type: "answer_delta"; part_index: number; text: string }
  | { type: "answer_reset"; part_index: number }
  | { type: "heartbeat" }
);

async function stream(id: string, after: number | undefined, signal: AbortSignal, onEvent: (event: LabEvent) => void) {
  const transport = new AbortController();
  const abort = () => transport.abort();
  signal.addEventListener("abort", abort, { once: true });
  let idle: ReturnType<typeof setTimeout>;
  const pulse = () => { clearTimeout(idle); idle = setTimeout(abort, 45000); };
  pulse();
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  try {
    if (signal.aborted) transport.abort();
    const response = await authenticatedStream(`/ai-lab/results/${id}/stream/${after === undefined ? "" : `?after_sequence=${after}`}`, transport.signal);
    if (!response.body || !response.headers.get("content-type")?.includes("application/x-ndjson")) throw new Error("Streaming unavailable");
    reader = response.body.getReader();
    const decoder = new TextDecoder();
    let pending = "";
    while (!signal.aborted) {
      const { done, value } = await reader.read();
      pulse();
      pending += decoder.decode(value, { stream: !done });
      if (pending.length > 1_000_000) throw new Error("Stream event too large");
      let newline: number;
      while ((newline = pending.indexOf("\n")) >= 0) {
        const raw = pending.slice(0, newline).trim();
        pending = pending.slice(newline + 1);
        if (!raw) continue;
        const event = JSON.parse(raw) as LabEvent;
        if (!Number.isSafeInteger(event.sequence) || event.sequence < 0 || typeof event.type !== "string") throw new Error("Invalid stream event");
        onEvent(event);
        if (event.type === "complete" || (event.type === "snapshot" && event.job.status !== "running")) return;
      }
      if (done) {
        if (pending.trim()) throw new Error("Incomplete stream event");
        return;
      }
    }
  } finally {
    clearTimeout(idle!);
    signal.removeEventListener("abort", abort);
    transport.abort();
    await reader?.cancel().catch(() => undefined);
    reader?.releaseLock();
  }
}

export const aiLabApi = {
  stream,
  cancel: async (id: string): Promise<void> => { await apiClient.post(`/ai-lab/results/${id}/cancel/`); },
  feedback: async (id: string): Promise<{ value: 1 | -1 | null }> => (await apiClient.get(`/ai-lab/results/${id}/feedback/`)).data,
  rate: async (id: string, value: 1 | -1): Promise<{ value: 1 | -1 }> => (await apiClient.post(`/ai-lab/results/${id}/feedback/`, { value })).data,
  active: async (): Promise<ActiveLabJob | null> => (await apiClient.get("/ai-lab/active/")).data.active_job,
  status: async (): Promise<LabStatus> => (await apiClient.get("/ai-lab/status/")).data,
  ask: async (question: string, history: string[], requestId?: string): Promise<{ job_id: string }> =>
    (await apiClient.post("/ai-lab/ask/", { question, model: LAB_MODEL, sources: ["uptodate"], history, request_id: requestId })).data,
  result: async (id: string, revision?: number): Promise<LabJob> =>
    (await apiClient.get(`/ai-lab/results/${id}/`, { params: revision === undefined ? undefined : { after_revision: revision } })).data,
};
