import {create} from "zustand";

import type {FlashcardFlowMode, FlashcardState, QuestionType, TargetCategory} from "../types/api";

type FlashcardsState = {
  step: "entry" | "category" | "cards";
  mode: FlashcardFlowMode;
  selectedQuestionType: QuestionType | null;
  selectedCategory: string;
  selectedLeitnerBox: number | null;
  categories: TargetCategory[];
  cards: FlashcardState[];
  revealed: boolean;
  reviewedCardIds: number[];
  setStep: (step: FlashcardsState["step"]) => void;
  setMode: (mode: FlashcardFlowMode) => void;
  setSelectedQuestionType: (value: QuestionType | null) => void;
  setSelectedCategory: (value: string) => void;
  setSelectedLeitnerBox: (value: number | null) => void;
  setCategories: (value: TargetCategory[]) => void;
  setCards: (value: FlashcardState[]) => void;
  setRevealed: (value: boolean) => void;
  pushReviewedCardId: (id: number) => void;
  resetReviewedCardIds: () => void;
  resetFlow: () => void;
};

const initialState = {
  step: "entry" as const,
  mode: "new" as FlashcardFlowMode,
  selectedQuestionType: null,
  selectedCategory: "",
  selectedLeitnerBox: null,
  categories: [] as TargetCategory[],
  cards: [] as FlashcardState[],
  revealed: false,
  reviewedCardIds: [] as number[],
};

export const useFlashcardsStore = create<FlashcardsState>((set) => ({
  ...initialState,
  setStep: (step) => set({step}),
  setMode: (mode) => set({mode}),
  setSelectedQuestionType: (selectedQuestionType) => set({selectedQuestionType}),
  setSelectedCategory: (selectedCategory) => set({selectedCategory}),
  setSelectedLeitnerBox: (selectedLeitnerBox) => set({selectedLeitnerBox}),
  setCategories: (categories) => set({categories}),
  setCards: (cards) => set({cards}),
  setRevealed: (revealed) => set({revealed}),
  pushReviewedCardId: (id) =>
    set((state) => ({
      reviewedCardIds: state.reviewedCardIds.includes(id) ? state.reviewedCardIds : [...state.reviewedCardIds, id],
    })),
  resetReviewedCardIds: () => set({reviewedCardIds: []}),
  resetFlow: () => set(initialState),
}));
