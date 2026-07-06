import {apiFetch, unwrapList} from "./client";
import type {
  AuthResponse,
  FlashcardBoxSummary,
  Dashboard,
  FlashcardState,
  GameAnswerResult,
  GameSession,
  LeaderboardEntry,
  Mistake,
  MyLeagueRank,
  Recommendation,
  QuestionType,
  Statistics,
  TargetCategory,
  Topic,
  TopicProgress,
  User,
} from "../types/api";

const json = (body: unknown): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body),
});

export const platformApi = {
  login(username: string, password: string) {
    return apiFetch("/auth/login/", json({username, password})) as Promise<AuthResponse>;
  },
  register(username: string, email: string, password: string) {
    return apiFetch("/auth/register/", json({username, email, password})) as Promise<AuthResponse>;
  },
  logout(token: string) {
    return apiFetch("/auth/logout/", {method: "POST"}, token) as Promise<null>;
  },
  me(token: string) {
    return apiFetch("/auth/me/", {}, token) as Promise<User>;
  },
  async topics(token?: string) {
    const payload = await apiFetch("/topics/", {}, token);
    return unwrapList<Topic>(payload);
  },
  async targetCategories(token?: string, source_type?: QuestionType) {
    const params = new URLSearchParams({product_id: "k_game"});
    if (source_type) params.set("source_type", source_type);
    const payload = await apiFetch(`/target-categories/?${params.toString()}`, {}, token);
    return unwrapList<TargetCategory>(payload);
  },
  dashboard(token: string) {
    return apiFetch("/me/dashboard/?product_id=k_game", {}, token) as Promise<Dashboard>;
  },
  recommendations(token: string) {
    return apiFetch("/me/recommendations/?product_id=k_game", {}, token) as Promise<Recommendation[]>;
  },
  async progress(token: string) {
    const payload = await apiFetch("/me/progress/?product_id=k_game", {}, token);
    return unwrapList<TopicProgress>(payload);
  },
  statistics(token: string) {
    return apiFetch("/me/statistics/?product_id=k_game", {}, token) as Promise<Statistics>;
  },
  async flashcards(token: string, box?: number, target_category_key = "", source_type: QuestionType = "brandGeneric") {
    const params = new URLSearchParams({product_id: "k_game"});
    if (box) params.set("box", String(box));
    if (target_category_key) params.set("target_category_key", target_category_key);
    params.set("source_type", source_type);
    const query = `?${params.toString()}`;
    const payload = await apiFetch(`/flashcards/${query}`, {}, token);
    return unwrapList<FlashcardState>(payload);
  },
  flashcardBoxes(token: string, target_category_key = "", source_type: QuestionType = "brandGeneric") {
    const params = new URLSearchParams({product_id: "k_game"});
    if (target_category_key) params.set("target_category_key", target_category_key);
    params.set("source_type", source_type);
    return apiFetch(`/flashcards/boxes/?${params.toString()}`, {}, token) as Promise<FlashcardBoxSummary>;
  },
  reviewFlashcard(token: string, id: number, rating: "known" | "unknown") {
    return apiFetch(`/flashcards/${id}/review/`, json({rating}), token) as Promise<FlashcardState>;
  },
  seedFlashcards(token: string, target_category_key = "", source_type: QuestionType = "brandGeneric", count = 0) {
    return apiFetch(
      "/flashcards/seed/",
      json({product_id: "k_game", count, target_category_key, source_type}),
      token,
    ) as Promise<FlashcardState[]>;
  },
  async mistakes(token: string) {
    const payload = await apiFetch("/me/mistakes/", {}, token);
    return unwrapList<Mistake>(payload);
  },
  startGame(
    token: string,
    question_type: QuestionType,
    mode: "random" | "category",
    count = 10,
    target_category_key = "",
  ) {
    return apiFetch(
      "/games/",
      json({topic_key: question_type, target_category_key, mode, count, timer_seconds: 30}),
      token,
    ) as Promise<GameSession>;
  },
  async pauseGame(token: string, gameId: number) {
    const payload = await apiFetch(`/games/${gameId}/pause/`, {method: "POST"}, token);
    return (payload as {game: GameSession}).game;
  },
  async resumeGame(token: string, gameId: number) {
    const payload = await apiFetch(`/games/${gameId}/resume/`, {method: "POST"}, token);
    return (payload as {game: GameSession}).game;
  },
  async extendGameTimer(token: string, gameId: number) {
    const payload = await apiFetch(`/games/${gameId}/extend-timer/`, {method: "POST"}, token);
    return (payload as {game: GameSession}).game;
  },
  answerQuestion(token: string, gameId: number, question_id: number, selected_answer: string) {
    return apiFetch(
      `/games/${gameId}/answer/`,
      json({question_id, selected_answer, client_answered_at: new Date().toISOString()}),
      token,
    ) as Promise<GameAnswerResult>;
  },
  finishGame(token: string, gameId: number) {
    return apiFetch(`/games/${gameId}/finish/`, {method: "POST"}, token) as Promise<GameSession>;
  },
  leaderboard(token: string) {
    return apiFetch("/league/?product_id=k_game", {}, token) as Promise<LeaderboardEntry[]>;
  },
  myLeagueRank(token: string) {
    return apiFetch("/league/me/?product_id=k_game", {}, token) as Promise<MyLeagueRank>;
  },
};
