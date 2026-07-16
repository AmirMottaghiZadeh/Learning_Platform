import {fireEvent, screen, waitFor} from "@testing-library/react-native";
import React from "react";

import {platformApi} from "../api/platform";
import {useAuth} from "../store/auth";
import {useFlashcardsStore} from "../store/flashcards";
import {renderWithQueryClient} from "../test/render";
import type {FlashcardFlowMode, FlashcardState, QuestionType} from "../types/api";
import {FlashcardsScreen} from "./FlashcardsScreen";

jest.mock("../api/platform", () => ({
  platformApi: {
    flashcardBoxes: jest.fn(),
    flashcards: jest.fn(),
    reviewFlashcard: jest.fn(),
  },
}));

jest.mock("../store/auth", () => ({
  useAuth: jest.fn(),
}));

const firstCard: FlashcardState = {
  id: 1,
  prompt: "سؤال اول",
  correct_answer: "پاسخ اول",
  feedback: "",
  source_type: "brandGeneric",
  target_category_key: "",
  target_category_label: "",
  is_in_leitner_box: true,
  box: 1,
  review_state: "learning",
  interval_days: 1,
  review_count: 0,
  lapse_count: 0,
  last_rating: "",
  schedule_rule_version: "",
  due_at: null,
  last_reviewed_at: null,
};
const secondCard: FlashcardState = {
  ...firstCard,
  id: 2,
  prompt: "سؤال دوم",
  correct_answer: "پاسخ دوم",
};
const api = platformApi as jest.Mocked<typeof platformApi>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("FlashcardsScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useFlashcardsStore.getState().resetFlow();
    mockUseAuth.mockReturnValue({
      token: "token-123",
      user: null,
      loading: false,
      error: null,
      signIn: jest.fn(),
      register: jest.fn(),
      signOut: jest.fn(),
    });
    api.flashcardBoxes.mockResolvedValue({
      new: 0,
      total: 2,
      boxes: [{box: 1, count: 2}],
    });
    api.flashcards.mockImplementation(
      async (
        _token: string,
        _mode: FlashcardFlowMode,
        _category: string | undefined,
        _questionType: QuestionType | undefined,
        excludedCardIds: number[] = [],
      ) =>
        excludedCardIds.includes(firstCard.id) ? [secondCard] : [firstCard, secondCard],
    );
    api.reviewFlashcard.mockResolvedValue(firstCard);
  });

  it("reveals a Leitner card and advances to the next card after review", async () => {
    renderWithQueryClient(<FlashcardsScreen />);

    expect(await screen.findByText("چه چیزی را می‌خواهی مرور کنی؟")).toBeTruthy();
    fireEvent.press(screen.getByText("جعبه لایتنر"));
    fireEvent.press(await screen.findByText("جعبه 1"));

    expect(await screen.findByText("سؤال اول")).toBeTruthy();
    const revealButtons = screen.getAllByRole("button", {name: "نمایش پاسخ"});
    fireEvent.press(revealButtons[revealButtons.length - 1]);
    expect(await screen.findByText("پاسخ اول")).toBeTruthy();
    const knownButtons = screen.getAllByRole("button", {name: "بلد بودم · خروج از جعبه"});
    fireEvent.press(knownButtons[knownButtons.length - 1]);

    await waitFor(() => expect(api.reviewFlashcard).toHaveBeenCalledWith("token-123", 1, "known"));
    expect(await screen.findByText("سؤال دوم")).toBeTruthy();
  });
});
