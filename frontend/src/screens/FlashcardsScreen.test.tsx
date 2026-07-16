import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {act, cleanup, fireEvent, render, screen, waitFor} from "@testing-library/react-native";
import React from "react";

import {platformApi} from "../api/platform";
import {useAuth} from "../store/auth";
import {useFlashcardsStore} from "../store/flashcards";
import type {FlashcardRating, FlashcardState} from "../types/api";
import {FlashcardsScreen} from "./FlashcardsScreen";

jest.mock("@tanstack/react-query", () => ({
  useMutation: jest.fn(),
  useQuery: jest.fn(),
  useQueryClient: jest.fn(),
}));

jest.mock("../api/platform", () => ({
  platformApi: {
    reviewFlashcard: jest.fn(),
  },
}));

jest.mock("../components/ui", () => ({
  ...jest.requireActual("../components/ui"),
  AnimatedEntrance: ({children}: {children: React.ReactNode}) => <>{children}</>,
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
const firstDeck = [firstCard, secondCard];
const remainingDeck = [secondCard];
const api = platformApi as jest.Mocked<typeof platformApi>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseQuery = useQuery as jest.MockedFunction<typeof useQuery>;
const mockUseMutation = useMutation as jest.MockedFunction<typeof useMutation>;
const mockUseQueryClient = useQueryClient as jest.MockedFunction<typeof useQueryClient>;

type TestQueryOptions = {
  queryKey: readonly unknown[];
};

type TestMutationOptions = {
  mutationFn: (variables: unknown) => Promise<unknown>;
  onSuccess?: (result: unknown, variables: unknown) => Promise<void> | void;
};

describe("FlashcardsScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useFlashcardsStore.setState({
      step: "cards",
      mode: "leitner",
      selectedQuestionType: null,
      selectedCategory: "",
      selectedLeitnerBox: 1,
      categories: [],
      cards: [],
      revealed: false,
      reviewedCardIds: [],
    });
    mockUseAuth.mockReturnValue({
      token: "token-123",
      user: null,
      loading: false,
      error: null,
      signIn: jest.fn(),
      register: jest.fn(),
      signOut: jest.fn(),
    });
    mockUseQueryClient.mockReturnValue({
      invalidateQueries: jest.fn(() => Promise.resolve()),
    } as never);
    mockUseQuery.mockImplementation(
      (({queryKey}: TestQueryOptions) => {
        if (queryKey[0] === "flashcard-boxes") {
          return {
            data: {new: 0, total: 2, boxes: [{box: 1, count: 2}]},
            error: null,
            isLoading: false,
            refetch: jest.fn(),
          };
        }
        if (queryKey[0] === "flashcards") {
          return {
            data: queryKey[6] === "1" ? remainingDeck : firstDeck,
            error: null,
            isLoading: false,
            refetch: jest.fn(),
          };
        }
        return {
          data: undefined,
          error: null,
          isLoading: false,
          refetch: jest.fn(),
        };
      }) as never,
    );
    mockUseMutation.mockImplementation(
      (({mutationFn, onSuccess}: TestMutationOptions) => ({
        error: null,
        isPending: false,
        mutate: (variables: unknown) => {
          void (async () => {
            const result = await mutationFn(variables);
            await act(async () => {
              await onSuccess?.(result, variables);
            });
          })();
        },
      })) as never,
    );
    api.reviewFlashcard.mockResolvedValue(firstCard);
  });

  afterEach(() => {
    cleanup();
    act(() => {
      useFlashcardsStore.getState().resetFlow();
    });
  });

  it("reveals a Leitner card and advances to the next card after review", async () => {
    render(<FlashcardsScreen />);

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
