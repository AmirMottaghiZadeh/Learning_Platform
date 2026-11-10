export type TabKey = "dashboard" | "lessons" | "profile";

export type ScreenKey =
  | TabKey
  | "quiz"
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
  | "downloads"
  | "settings"
  | "support"
  | "aiLab"
  | "devices"
  | "notifications"
  | "plans"
  | "education"
  | "guidelines"
  | "diseasesConditions"
  | "calculator"
  | "calculatorDomain"
  | "calculatorDetail"
  | "medscapeOutline"
  | "medscapeArticle"
  | "medscapeSpecialty";

export const TAB_ORDER: TabKey[] = ["dashboard", "lessons", "profile"];

/** Reserved for tabs shipped behind a server feature flag. */
export const LOCKED_TABS: TabKey[] = [];
