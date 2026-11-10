import { create } from "zustand";
import type { LabJob, LabModel } from "@/api/aiLab";
import { useAuth } from "@/store/auth";

export type LabTurn = LabJob & { id: string; question: string; model: LabModel; jobId?: string };

/** Memory only, account scoped. Never persist prompts or model responses to disk. */
export const useAiLab = create<{
  owner: number | null; turns: LabTurn[]; draft: string;
  reset: (owner: number | null) => void;
  patch: (id: string, values: Partial<LabTurn>) => void;
}>((set) => ({
  owner: null, turns: [], draft: "",
  reset: (owner) => set({ owner, turns: [], draft: "" }),
  patch: (id, values) => set((s) => ({ turns: s.turns.map((t) => t.id === id ? { ...t, ...values } : t) })),
}));

useAuth.subscribe((state, previous) => {
  if (state.status === "signedOut" || state.user?.id !== previous.user?.id) {
    useAiLab.getState().reset(state.status === "signedOut" ? null : state.user?.id ?? null);
  }
});
