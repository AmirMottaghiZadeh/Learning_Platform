import { apiClient, unwrapList } from "./client";
import {
  AuthTokenResponse,
  BoxCard,
  BoxRating,
  CalculatorCategoryRef,
  CalculatorDetail,
  CalculatorListItem,
  Chapter,
  Dashboard,
  DeckOverview,
  DeckProgress,
  LeitnerOverview,
  LessonDrug,
  LessonDrugSearchResult,
  LessonGroup,
  LexicompDrug,
  LexicompInteraction,
  MedscapeArticleDetail,
  MedscapeArticleListItem,
  MedscapeCategoryNode,
  MedscapeImage,
  MedscapeKind,
  Mistake,
  OfflineDataset,
  OfflineLicense,
  OfflinePackageInfo,
  OfflinePackageUrls,
  PlanToday,
  QuizAnswerResult,
  QuizOverview,
  QuizPreview,
  QuizResult,
  QuizSession,
  Statistics,
  StudyPlan,
  StudyPlanItem,
  TopicDeck,
  UptodateArticle,
  UptodateImage,
  UptodateSearchResult,
  OtpPurpose,
  OtpRequestResponse,
  ReleaseCheck,
  AppAnnouncement,
  AnnouncementEvent,
  User,
} from "./types";

// --- auth ---------------------------------------------------------------

export const authApi = {
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
  // SMS code for signing up ("signup") or for a forgotten password ("reset").
  requestOtp: (body: { phone: string; purpose: OtpPurpose }) =>
    apiClient.post<OtpRequestResponse>("/auth/otp/request/", body).then((r) => r.data),
  verifyOtp: (body: { phone: string; purpose: OtpPurpose; code: string; device_name?: string }) =>
    apiClient.post<AuthTokenResponse>("/auth/otp/verify/", body).then((r) => r.data),
  setPassword: (body: { new_password: string; new_password_confirm: string; name?: string; current_password?: string }) =>
    apiClient.post<User>("/auth/password/set/", body).then((r) => r.data),
  onboarding: (body: {
    study_field: string;
    study_goal: string;
    study_level: string;
    display_name?: string;
    language?: string;
    // The study plan the answers make (backend progress.planning.plan_from_onboarding).
    exam_date?: string | null;
    daily_minutes?: number;
    study_days?: boolean[];
    category_keys?: string[];
  }) => apiClient.post<User>("/auth/onboarding/", body).then((r) => r.data),
};

// Guest access, switched on from the console (/ops/access/): the app opens
// without signing in, each visitor on a throwaway account of their own.
export const guestApi = {
  status: () =>
    apiClient.get<{ enabled: boolean }>("/guest/status/", { skipAuth: true } as never).then((r) => r.data),
  start: () =>
    apiClient.post<AuthTokenResponse>("/guest/session/", null, { skipAuth: true } as never).then((r) => r.data),
};

// The app's published versions (backend apps.releases), checked on opening.
export const releaseApi = {
  check: (platform: "android" | "ios", versionCode: number) =>
    apiClient
      .get<ReleaseCheck>("/app/release/", {
        params: { platform, version_code: versionCode },
        skipAuth: true,
      } as never)
      .then((r) => r.data),
};

// Messages from the admin (backend apps.announcements), shown on home.
export const announcementsApi = {
  list: (versionCode: number, pwaState: "browser" | "standalone" | "native") =>
    apiClient.get<AppAnnouncement[]>("/announcements/", { params: { version_code: versionCode, pwa_state: pwaState } }).then((r) => r.data),
  event: (id: number, event: AnnouncementEvent) =>
    apiClient.post(`/announcements/${id}/event/`, { event }).then(() => undefined),
};

// --- drug knowledge ---------------------------------------------------

// --- lessons -------------------------------------------------------------

export const lessonsApi = {
  groups: () => apiClient.get<LessonGroup[]>("/lessons/groups/").then((r) => r.data),
  chapter: (code: string) =>
    apiClient.get<Chapter>(`/lessons/chapters/${code}/`).then((r) => r.data),
  saveProgress: (code: string, body: { drug_slug?: string; scroll_pct?: number }) =>
    apiClient.post<Chapter>(`/lessons/chapters/${code}/`, body).then((r) => r.data),
  drug: (slug: string) => apiClient.get<LessonDrug>(`/lessons/drugs/${slug}/`).then((r) => r.data),
  // Drugs by English or Persian name, best match first.
  search: (q: string) =>
    apiClient.get<LessonDrugSearchResult[]>("/lessons/search/", { params: { q } }).then((r) => r.data),
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
  savePlan: (body: Omit<StudyPlan, "fits_deadline" | "updated_at">) =>
    apiClient.put<StudyPlan>("/me/plan/", body).then((r) => r.data),
  planToday: () => apiClient.get<PlanToday>("/me/plan/today/").then((r) => r.data),
  // The home screen's plan box: today and this week, without every topic's progress.
  planTodayBrief: () =>
    apiClient.get<PlanToday>("/me/plan/today/", { params: { brief: 1 } }).then((r) => r.data),
  completePlanItem: (id: number) =>
    apiClient.post<StudyPlanItem>(`/me/plan/items/${id}/complete/`).then((r) => r.data),
  skipPlanItem: (id: number) =>
    apiClient.post<StudyPlanItem>(`/me/plan/items/${id}/skip/`).then((r) => r.data),
};

// --- flashcards & quiz (locked -> 503 until enabled server-side) ------

export const flashcardsApi = {
  decks: () => apiClient.get<DeckOverview>("/flashcards/decks/").then((r) => r.data),
  deck: (topic: string) => apiClient.get<TopicDeck>(`/flashcards/decks/${topic}/`).then((r) => r.data),
  // "hard" is "یادم نبود": the card goes in the Leitner box.
  answer: (topic: string, drugSlug: string, section: string, rating: "easy" | "hard") =>
    apiClient
      .post<DeckProgress>(`/flashcards/decks/${topic}/answer/`, { drug_slug: drugSlug, section, rating })
      .then((r) => r.data),
  // The Leitner box (backend apps.flashcards.leitner).
  leitner: () => apiClient.get<LeitnerOverview>("/flashcards/leitner/").then((r) => r.data),
  /** Today's review, or every card of one drawer. */
  leitnerCards: (box?: number) =>
    apiClient
      .get<BoxCard[]>("/flashcards/leitner/cards/", { params: box ? { box } : {} })
      .then((r) => r.data),
  leitnerReview: (id: number, rating: BoxRating) =>
    apiClient.post<BoxCard>(`/flashcards/leitner/cards/${id}/review/`, { rating }).then((r) => r.data),
  restart: (topic: string) =>
    apiClient.post<DeckProgress>(`/flashcards/decks/${topic}/restart/`).then((r) => r.data),
};

export const uptodateApi = {
  search: (search: string, limit = 25) =>
    apiClient
      .get<UptodateSearchResult[]>("/uptodate/topics/", { params: { search, limit } })
      .then((r) => r.data),
  topic: (id: string) =>
    apiClient.get<UptodateArticle>(`/uptodate/topics/${id}/`).then((r) => r.data),
  image: (id: string) =>
    apiClient.get<UptodateImage>(`/uptodate/images/${id}/`).then((r) => r.data),
};

export const lexicompApi = {
  search: (search: string, limit = 20) =>
    apiClient
      .get<LexicompDrug[]>("/lexicomp/drugs/", { params: { search, limit } })
      .then((r) => r.data),
  checkInteractions: (genericIds: number[]) =>
    apiClient
      .post<LexicompInteraction[]>("/lexicomp/interactions/", { generic_ids: genericIds })
      .then((r) => r.data),
};

// Encrypted packages for reading UpToDate/Lexicomp without the network (see
// src/offline). Download links point straight at the bucket.
export const offlineApi = {
  packages: () => apiClient.get<OfflinePackageInfo[]>("/offline/packages/").then((r) => r.data),
  urls: (dataset: OfflineDataset, build?: string) =>
    apiClient
      .post<OfflinePackageUrls>(`/offline/packages/${dataset}/urls/`, build ? { build } : {})
      .then((r) => r.data),
  license: (dataset: OfflineDataset, build: string, publicKey?: string) =>
    apiClient
      .post<OfflineLicense>(`/offline/packages/${dataset}/license/`, { build, public_key: publicKey ?? "" })
      .then((r) => r.data),
};

export const calculatorsApi = {
  // Unpaginated by design -- the client groups the full set by clinical
  // category and filters it client-side (see calculatorCategories.ts).
  list: () => apiClient.get("/calculators/").then((r) => unwrapList<CalculatorListItem>(r.data)),
  // The full category tree, independent of the calculator list -- see
  // calculatorCategories.ts for why grouping needs this rather than just
  // each calculator's own (few) category tags.
  categories: () =>
    apiClient.get("/calculators/categories/").then((r) => unwrapList<CalculatorCategoryRef>(r.data)),
  detail: (slug: string) =>
    apiClient.get<CalculatorDetail>(`/calculators/${slug}/`).then((r) => r.data),
};

export const medscapeApi = {
  // Too many disease articles (~3200) to fetch as one list and group
  // client-side the way calculators does -- tree() returns just the small
  // category/specialty taxonomy with counts; articles are fetched by
  // specialty or by search, both on demand.
  tree: (kind: MedscapeKind) =>
    apiClient.get<MedscapeCategoryNode[]>("/medscape/tree/", { params: { kind } }).then((r) => r.data),
  bySpecialty: (kind: MedscapeKind, category: string, specialty: string) =>
    apiClient
      .get("/medscape/articles/", { params: { kind, category, specialty } })
      .then((r) => unwrapList<MedscapeArticleListItem>(r.data)),
  // Only meaningful where latest_update is populated (guidelines with a
  // "Latest Guidance Updates"-style section -- about a quarter of them);
  // rows without one are excluded server-side rather than sorted last.
  recentlyUpdated: (kind: MedscapeKind, category: string, specialty: string, limit = 8) =>
    apiClient
      .get("/medscape/articles/", { params: { kind, category, specialty, recent: 1, limit } })
      .then((r) => unwrapList<MedscapeArticleListItem>(r.data)),
  search: (kind: MedscapeKind, search: string) =>
    apiClient
      .get("/medscape/articles/", { params: { kind, search } })
      .then((r) => unwrapList<MedscapeArticleListItem>(r.data)),
  detail: (slug: string) =>
    apiClient.get<MedscapeArticleDetail>(`/medscape/articles/${slug}/`).then((r) => r.data),
  // Images are fetched as base64 (same shape as uptodateApi.image) rather
  // than pointing <Image> straight at the API URL, since that would need
  // the auth header React Native's Image doesn't attach for us.
  image: (id: number) =>
    apiClient.get<MedscapeImage>(`/medscape/images/${id}/`).then((r) => r.data),
};

export const quizApi = {
  overview: () => apiClient.get<QuizOverview>("/quiz/overview/").then((r) => r.data),
  preview: (category: string, atcCode: string, count: number) =>
    apiClient
      .get<QuizPreview>("/quiz/preview/", { params: { category, atc_code: atcCode, count } })
      .then((r) => r.data),
  start: (
    body: { category: string; atc_code?: string; count: number } | { ingredient_slug: string },
  ) => apiClient.post<QuizSession>("/quiz/start/", body).then((r) => r.data),
  answer: (
    sessionId: number,
    body: { question_id: number; selected_index: number; client_answered_at?: string },
  ) =>
    apiClient
      .post<QuizAnswerResult>(`/quiz/${sessionId}/answer/`, body)
      .then((r) => r.data),
  finish: (sessionId: number) =>
    apiClient.post<QuizResult>(`/quiz/${sessionId}/finish/`).then((r) => r.data),
  reviewMistakes: (sessionId: number) =>
    apiClient.post<QuizSession>(`/quiz/${sessionId}/review-mistakes/`).then((r) => r.data),
};
