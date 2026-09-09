import { apiClient, unwrapList } from "./client";
import {
  AtcCode,
  AuthTokenResponse,
  BoxSummary,
  Chapter,
  Dashboard,
  IngredientDetail,
  IngredientListItem,
  LeitnerCard,
  LessonGroup,
  Mistake,
  QuizAnswerResult,
  QuizResult,
  QuizSession,
  Statistics,
  StudyPlan,
  UptodateArticle,
  UptodateTopic,
  User,
} from "./types";

// --- auth ---------------------------------------------------------------

export const authApi = {
  register: (body: { name: string; email: string; password: string; password_confirm: string }) =>
    apiClient.post<AuthTokenResponse>("/auth/register/", body).then((r) => r.data),
  login: (body: { username: string; password: string; device_name?: string }) =>
    apiClient.post<AuthTokenResponse>("/auth/login/", body).then((r) => r.data),
  refresh: (refresh_token: string) =>
    apiClient
      .post<AuthTokenResponse>("/auth/refresh/", { refresh_token }, {
        skipAuth: true,
      } as never)
      .then((r) => r.data),
  logout: () => apiClient.post("/auth/logout/").then((r) => r.data),
  me: () => apiClient.get<User>("/auth/me/").then((r) => r.data),
  onboarding: (body: {
    study_field: string;
    study_goal: string;
    study_level: string;
    display_name?: string;
    language?: string;
  }) => apiClient.post<User>("/auth/onboarding/", body).then((r) => r.data),
};

// --- drug knowledge ---------------------------------------------------

export const drugsApi = {
  list: (params?: { search?: string; atc?: string; page?: number }) =>
    apiClient
      .get("/drugs/", { params })
      .then((r) => ({
        results: unwrapList<IngredientListItem>(r.data),
        count: (r.data as { count?: number }).count ?? 0,
        next: (r.data as { next?: string | null }).next ?? null,
      })),
  detail: (slug: string) =>
    apiClient.get<IngredientDetail>(`/drugs/${slug}/`).then((r) => r.data),
  atc: (prefix?: string) =>
    apiClient.get<AtcCode[]>("/atc/", { params: { prefix } }).then((r) => r.data),
};

// --- lessons -------------------------------------------------------------

export const lessonsApi = {
  groups: () => apiClient.get<LessonGroup[]>("/lessons/groups/").then((r) => r.data),
  chapter: (code: string) =>
    apiClient.get<Chapter>(`/lessons/chapters/${code}/`).then((r) => r.data),
  saveProgress: (code: string, body: { drug_slug?: string; scroll_pct?: number }) =>
    apiClient.post<Chapter>(`/lessons/chapters/${code}/`, body).then((r) => r.data),
};

// --- me ---------------------------------------------------------------

export const meApi = {
  dashboard: () => apiClient.get<Dashboard>("/me/dashboard/").then((r) => r.data),
  statistics: () => apiClient.get<Statistics>("/me/statistics/").then((r) => r.data),
  mistakes: () => apiClient.get<Mistake[]>("/me/mistakes/").then((r) => r.data),
  resolveMistake: (id: number) =>
    apiClient.post<Mistake>(`/me/mistakes/${id}/resolve/`).then((r) => r.data),
  restoreMistakes: () =>
    apiClient.post<Mistake[]>("/me/mistakes/restore/").then((r) => r.data),
  plan: () => apiClient.get<StudyPlan>("/me/plan/").then((r) => r.data),
  savePlan: (body: StudyPlan) =>
    apiClient.put<StudyPlan>("/me/plan/", body).then((r) => r.data),
};

// --- flashcards & quiz (locked -> 503 until enabled server-side) ------

export const flashcardsApi = {
  due: () => apiClient.get<LeitnerCard[]>("/flashcards/").then((r) => r.data),
  boxes: () => apiClient.get<BoxSummary[]>("/flashcards/boxes/").then((r) => r.data),
  seed: () => apiClient.post("/flashcards/seed/").then((r) => r.data),
  review: (id: number, rating: "easy" | "hard") =>
    apiClient.post<LeitnerCard>(`/flashcards/${id}/review/`, { rating }).then((r) => r.data),
};

export const uptodateApi = {
  search: (search: string, limit = 25) =>
    apiClient
      .get<UptodateTopic[]>("/uptodate/topics/", { params: { search, limit } })
      .then((r) => r.data),
  topic: (id: string) =>
    apiClient.get<UptodateArticle>(`/uptodate/topics/${id}/`).then((r) => r.data),
};

export const quizApi = {
  start: (body: { category: string; count: number }) =>
    apiClient.post<QuizSession>("/quiz/start/", body).then((r) => r.data),
  answer: (
    sessionId: number,
    body: { question_id: number; selected_index: number; client_answered_at?: string },
  ) =>
    apiClient
      .post<QuizAnswerResult>(`/quiz/${sessionId}/answer/`, body)
      .then((r) => r.data),
  finish: (sessionId: number) =>
    apiClient.post<QuizResult>(`/quiz/${sessionId}/finish/`).then((r) => r.data),
};
