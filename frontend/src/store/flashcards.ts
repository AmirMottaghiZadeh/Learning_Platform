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
  setStep: (step: FlashcardsState["step"]) => void;
  setMode: (mode: FlashcardFlowMode) => void;
  setSelectedQuestionType: (value: QuestionType | null) => void;
  setSelectedCategory: (value: string) => void;
  setSelectedLeitnerBox: (value: number | null) => void;
  setCategories: (value: TargetCategory[]) => void;
  setCards: (value: FlashcardState[]) => void;
  appendCards: (value: FlashcardState[]) => void;
  removeCard: (id: number) => void;
  prependCard: (card: FlashcardState) => void;
  setRevealed: (value: boolean) => void;
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
  appendCards: (cards) =>
    set((state) => {
      const knownIds = new Set(state.cards.map((card) => card.id));
      return {
        cards: [...state.cards, ...cards.filter((card) => !knownIds.has(card.id))],
      };
    }),
  removeCard: (id) =>
    set((state) => ({
      cards: state.cards.filter((card) => card.id !== id),
    })),
  prependCard: (card) =>
    set((state) => ({
      cards: state.cards.some((item) => item.id === card.id)
        ? state.cards
        : [card, ...state.cards],
    })),
  setRevealed: (revealed) => set({revealed}),
  resetFlow: () => set(initialState),
}));
