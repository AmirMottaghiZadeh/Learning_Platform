export type TabKey = "dashboard" | "lessons" | "flashcards" | "quiz" | "profile";

export type ScreenKey =
  | TabKey
  | "auth"
  | "onboarding"
  | "lessonList"
  | "lessonDetail"
  | "mistakes"
  | "statistics"
  | "planning"
  | "uptodate"
  | "uptodateArticle";

export const TAB_ORDER: TabKey[] = ["dashboard", "lessons", "flashcards", "quiz", "profile"];

/** Tabs that are built but locked server-side (feature flags off). */
export const LOCKED_TABS: TabKey[] = ["flashcards", "quiz"];

export type ScreenParams = {
  lessonDetail: { code: string };
  [key: string]: Record<string, unknown> | undefined;
};
