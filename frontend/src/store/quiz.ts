import {create} from "zustand";

import type {QuestionType, QuizReminder, Topic} from "../types/api";

export const AVAILABLE_QUIZ_TYPES: Array<{key: QuestionType; label: string}> = [
  {key: "brandGeneric", label: "نام تجاری"},
  {key: "timing", label: "با غذا / بی غذا"},
];

type QuizSetupState = {
  selectedQuestionTypeKey: QuestionType;
  selectedQuestionTypeId: QuestionType;
  selectedTopicId: number | null;
  selectedMode: "random" | "category";
  selectedCategoryKey: string;
  selectedCount: number;
  reminderPanelOpen: boolean;
  setQuestionType: (topic: Topic) => void;
  syncTopicFromTopics: (topics: Topic[]) => void;
  setMode: (mode: "random" | "category") => void;
  setCategoryKey: (categoryKey: string) => void;
  setCount: (count: number) => void;
  setReminderPanelOpen: (open: boolean) => void;
  applyReminder: (reminder: QuizReminder) => void;
  resetSetup: () => void;
};

const initialState = {
  selectedQuestionTypeKey: "brandGeneric" as QuestionType,
  selectedQuestionTypeId: "brandGeneric" as QuestionType,
  selectedTopicId: null,
  selectedMode: "random" as const,
  selectedCategoryKey: "",
  selectedCount: 10,
  reminderPanelOpen: false,
};

const ALLOWED_QUESTION_TYPES = new Set<QuestionType>(AVAILABLE_QUIZ_TYPES.map((item) => item.key));

export const useQuizStore = create<QuizSetupState>((set) => ({
  ...initialState,
  setQuestionType: (topic) =>
    set({
      selectedQuestionTypeKey: topic.key as QuestionType,
      selectedQuestionTypeId: topic.key as QuestionType,
      selectedTopicId: topic.id,
      selectedCategoryKey: "",
    }),
  syncTopicFromTopics: (topics) =>
    set((state) => {
      const nextTopic =
        topics.find((item) => item.id === state.selectedTopicId) ??
        topics.find((item) => item.key === state.selectedQuestionTypeKey) ??
        topics.find((item) => ALLOWED_QUESTION_TYPES.has(item.key as QuestionType));
      if (!nextTopic) return state;
      return {
        selectedQuestionTypeKey: nextTopic.key as QuestionType,
        selectedQuestionTypeId: nextTopic.key as QuestionType,
        selectedTopicId: nextTopic.id,
      };
    }),
  setMode: (selectedMode) => set({selectedMode}),
  setCategoryKey: (selectedCategoryKey) => set({selectedCategoryKey}),
  setCount: (selectedCount) => set({selectedCount}),
  setReminderPanelOpen: (reminderPanelOpen) => set({reminderPanelOpen}),
  applyReminder: (reminder) =>
    set({
      selectedQuestionTypeKey: reminder.question_type as QuestionType,
      selectedQuestionTypeId: reminder.question_type as QuestionType,
      reminderPanelOpen: true,
    }),
  resetSetup: () => set(initialState),
}));
