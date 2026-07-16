import AsyncStorage from "@react-native-async-storage/async-storage";
import {fireEvent, screen, waitFor} from "@testing-library/react-native";
import React from "react";

import {platformApi} from "../api/platform";
import {useAuth} from "../store/auth";
import {useQuizStore} from "../store/quiz";
import {renderWithQueryClient} from "../test/render";
import type {GameQuestion, GameSession, Topic, User} from "../types/api";
import {QuizScreen} from "./QuizScreen";

jest.mock("../api/platform", () => ({
  platformApi: {
    answerQuestion: jest.fn(),
    targetCategories: jest.fn(),
    topics: jest.fn(),
    startGame: jest.fn(),
  },
}));

jest.mock("../store/auth", () => ({
  useAuth: jest.fn(),
}));

const user: User = {
  id: 1,
  first_name: "Ali",
  last_name: "Ahmadi",
  username: "learner",
  email: "learner@example.com",
};
const topic: Topic = {
  id: 10,
  key: "brandGeneric",
  label: "نام تجاری",
  detail: "برند و ژنریک",
};
const question: GameQuestion = {
  id: 20,
  order: 1,
  question_type: "brandGeneric",
  interaction_type: "multiple_choice",
  option_layout: "list",
  instruction: "",
  prompt: "نام ژنریک دارو چیست؟",
  chip: "",
  explanation: "توضیح پاسخ",
  options: ["پاسخ درست", "پاسخ نادرست"],
  timer_base_seconds: 30,
  timer_extension_seconds: 30,
  timer_total_seconds: 30,
  timer_remaining_seconds: 30,
  timer_extension_used: false,
  timer_extension_available: true,
};
const session: GameSession = {
  id: 30,
  topic_key: "brandGeneric",
  target_category_key: "",
  mode: "random",
  total_questions: 10,
  timer_seconds: 30,
  score: 0,
  correct_count: 0,
  streak: 0,
  status: "active",
  paused_at: null,
  total_paused_seconds: 0,
  is_finished: false,
  current_question: question,
};
const storage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;
const api = platformApi as jest.Mocked<typeof platformApi>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("QuizScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useQuizStore.getState().resetSetup();
    storage.getItem.mockResolvedValue(null);
    mockUseAuth.mockReturnValue({
      token: "token-123",
      user,
      loading: false,
      error: null,
      signIn: jest.fn(),
      register: jest.fn(),
      signOut: jest.fn(),
    });
    api.topics.mockResolvedValue([topic]);
    api.targetCategories.mockResolvedValue([]);
    api.startGame.mockResolvedValue(session);
    api.answerQuestion.mockResolvedValue({
      answer: {
        id: 40,
        is_correct: true,
        time_expired: false,
        correct_answer: "پاسخ درست",
        remaining_seconds: 24,
        score_delta: 10,
        xp_delta: 5,
        scoring_rule_version: "v1",
      },
      game: session,
    });
  });

  it("submits a selected answer and shows correct feedback", async () => {
    renderWithQueryClient(<QuizScreen />);

    fireEvent.press(await screen.findByText("نام تجاری"));
    fireEvent.press(screen.getByText("تصادفی"));
    fireEvent.press(screen.getByText("شروع آزمون"));

    expect(await screen.findByText("نام ژنریک دارو چیست؟")).toBeTruthy();
    fireEvent.press(screen.getByText("پاسخ درست"));

    await waitFor(() =>
      expect(api.answerQuestion).toHaveBeenCalledWith("token-123", 30, 20, "پاسخ درست"),
    );
    expect(await screen.findByText("آفرین! پاسخ درست بود.")).toBeTruthy();
  });
});
