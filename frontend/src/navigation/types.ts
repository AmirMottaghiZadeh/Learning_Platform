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
  | "planningSetup"
  | "uptodate"
  | "uptodateOutline"
  | "uptodateArticle"
  | "lexicomp"
  | "education"
  | "guidelines"
  | "diseasesConditions"
  | "calculator"
  | "calculatorDomain"
  | "calculatorDetail"
  | "medscapeArticle"
  | "medscapeSpecialty";

export const TAB_ORDER: TabKey[] = ["dashboard", "lessons", "flashcards", "quiz", "profile"];

/** Tabs that are built but locked server-side (feature flags off). Both quiz
 * and flashcards are live now (QUIZ_API_ENABLED / FLASHCARDS_API_ENABLED) --
 * kept as an empty list, not removed, so the next tab that ships behind a
 * flag has somewhere to go. */
export const LOCKED_TABS: TabKey[] = [];

export type ScreenParams = {
  lessonDetail: { code: string };
  [key: string]: Record<string, unknown> | undefined;
};
