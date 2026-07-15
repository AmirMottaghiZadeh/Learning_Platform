import {apiClient, unwrapList, withToken} from "./client";
import type {
  AuthResponse,
  Dashboard,
  FlashcardBoxSummary,
  FlashcardDeckSummary,
  FlashcardRating,
  FlashcardState,
  GameAnswerResult,
  GameSession,
  LeaderboardEntry,
  LeagueFullSummary,
  Mistake,
  MyLeagueRank,
  PasswordResetResponse,
  QuestionType,
  QuizHistorySession,
  QuizReminder,
  RegisterPayload,
  Statistics,
  TargetCategory,
  Topic,
  TopicProgress,
  User,
} from "../types/api";

export const platformApi = {
  async login(username: string, password: string) {
    const {data} = await apiClient.post<AuthResponse>("/auth/login/", {username, password});
    return data;
  },
  async register(payload: RegisterPayload) {
    const {data} = await apiClient.post<AuthResponse>("/auth/register/", payload);
    return data;
  },
  async requestPasswordReset(email: string) {
    const {data} = await apiClient.post<PasswordResetResponse>("/auth/password-reset/", {email});
    return data;
  },
  async logout(token: string) {
    await apiClient.post("/auth/logout/", {}, withToken(token));
    return null;
  },
  async me(token: string) {
    const {data} = await apiClient.get<User>("/auth/me/", withToken(token));
    return data;
  },
  async topics(token?: string) {
    const {data} = await apiClient.get("/topics/", withToken(token));
    return unwrapList<Topic>(data);
  },
  async targetCategories(token?: string, source_type?: QuestionType) {
    const params = new URLSearchParams({product_id: "pharmexa"});
    if (source_type) params.set("source_type", source_type);
    const {data} = await apiClient.get(`/target-categories/?${params.toString()}`, withToken(token));
    return unwrapList<TargetCategory>(data);
  },
  async dashboard(token: string) {
    const {data} = await apiClient.get<Dashboard>("/me/dashboard/?product_id=pharmexa", withToken(token));
    return data;
  },
  async progress(token: string) {
    const {data} = await apiClient.get("/me/progress/?product_id=pharmexa", withToken(token));
    return unwrapList<TopicProgress>(data);
  },
  async statistics(token: string) {
    const {data} = await apiClient.get<Statistics>("/me/statistics/?product_id=pharmexa", withToken(token));
    return data;
  },
  async flashcards(
    token: string,
    mode: "new" | "leitner",
    target_category_key = "",
    source_type?: QuestionType,
    exclude_ids: number[] = [],
    box?: number | null,
  ) {
    const params = new URLSearchParams({product_id: "pharmexa", mode});
    if (mode === "new") {
      if (target_category_key) params.set("target_category_key", target_category_key);
      if (source_type) params.set("source_type", source_type);
    }
    if (mode === "leitner" && box) params.set("box", String(box));
    if (exclude_ids.length) params.set("exclude_ids", exclude_ids.join(","));
    const {data} = await apiClient.get(`/flashcards/?${params.toString()}`, withToken(token));
    return unwrapList<FlashcardState>(data);
  },
  async flashcardBoxes(token: string) {
    const {data} = await apiClient.get<FlashcardBoxSummary>(
      "/flashcards/boxes/?product_id=pharmexa",
      withToken(token),
    );
    return data;
  },
  async flashcardDeckSummary(token: string, target_category_key = "", source_type: QuestionType = "brandGeneric") {
    const params = new URLSearchParams({product_id: "pharmexa", source_type});
    if (target_category_key) params.set("target_category_key", target_category_key);
    const {data} = await apiClient.get<FlashcardDeckSummary>(
      `/flashcards/decks/?${params.toString()}`,
      withToken(token),
    );
    return data;
  },
  async reviewFlashcard(token: string, id: number, rating: FlashcardRating) {
    const {data} = await apiClient.post<FlashcardState>(`/flashcards/${id}/review/`, {rating}, withToken(token));
    return data;
  },
  async seedFlashcards(token: string, target_category_key = "", source_type: QuestionType = "brandGeneric") {
    const {data} = await apiClient.post<FlashcardState[]>(
      "/flashcards/seed/",
      {product_id: "pharmexa", target_category_key, source_type},
      withToken(token),
    );
    return data;
  },
  async mistakes(token: string) {
    const {data} = await apiClient.get("/me/mistakes/", withToken(token));
    return unwrapList<Mistake>(data);
  },
  async startGame(
    token: string,
    topic_id: number,
    mode: "random" | "category",
    count = 10,
    target_category_key = "",
  ) {
    const {data} = await apiClient.post<GameSession>(
      "/games/",
      {topic_id, target_category_key, mode, count, timer_seconds: 30},
      withToken(token),
    );
    return data;
  },
  async pauseGame(token: string, gameId: number) {
    const {data} = await apiClient.post<{game: GameSession}>(`/games/${gameId}/pause/`, {}, withToken(token));
    return data.game;
  },
  async resumeGame(token: string, gameId: number) {
    const {data} = await apiClient.post<{game: GameSession}>(`/games/${gameId}/resume/`, {}, withToken(token));
    return data.game;
  },
  async extendGameTimer(token: string, gameId: number) {
    const {data} = await apiClient.post<{game: GameSession}>(`/games/${gameId}/extend-timer/`, {}, withToken(token));
    return data.game;
  },
  async answerQuestion(token: string, gameId: number, question_id: number, selected_answer: string) {
    const {data} = await apiClient.post<GameAnswerResult>(
      `/games/${gameId}/answer/`,
      {question_id, selected_answer, client_answered_at: new Date().toISOString()},
      withToken(token),
    );
    return data;
  },
  async finishGame(token: string, gameId: number) {
    const {data} = await apiClient.post<GameSession>(`/games/${gameId}/finish/`, {}, withToken(token));
    return data;
  },
  async quizHistory(token: string) {
    const {data} = await apiClient.get("/me/quiz-history/", withToken(token));
    return unwrapList<QuizHistorySession>(data);
  },
  async quizReminders(token: string) {
    const {data} = await apiClient.get("/me/quiz-reminders/", withToken(token));
    return unwrapList<QuizReminder>(data);
  },
  async createQuizReminder(
    token: string,
    payload: {
      game_session_id?: number;
      game_question_id?: number;
      knowledge_source_id?: number;
      question_type: string;
      prompt: string;
      selected_answer?: string;
      correct_answer: string;
      explanation?: string;
      options?: string[];
    },
  ) {
    const {data} = await apiClient.post<QuizReminder>("/me/quiz-reminders/", payload, withToken(token));
    return data;
  },
  async updateQuizReminder(token: string, reminderId: number, is_reviewed: boolean) {
    const {data} = await apiClient.patch<QuizReminder>(
      `/me/quiz-reminders/${reminderId}/`,
      {is_reviewed},
      withToken(token),
    );
    return data;
  },
  async leaderboard(token: string) {
    const {data} = await apiClient.get<LeaderboardEntry[]>("/league/?product_id=pharmexa", withToken(token));
    return data;
  },
  async myLeagueRank(token: string) {
    const {data} = await apiClient.get<MyLeagueRank>("/league/me/?product_id=pharmexa", withToken(token));
    return data;
  },
  async leagueSummary(token: string) {
    const {data} = await apiClient.get<LeagueFullSummary>("/league/summary/?product_id=pharmexa", withToken(token));
    return data;
  },
};
