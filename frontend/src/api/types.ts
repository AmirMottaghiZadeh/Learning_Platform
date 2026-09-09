/** Response shapes — mirror `docs/api-contract.md`. */

export type StudyField = "" | "pharmacy" | "medicine" | "nursing";
export type StudyGoal = "" | "residency" | "final" | "clinical";
export type StudyLevel = "" | "beginner" | "intermediate" | "advanced";

export interface LearnerProfile {
  display_name: string;
  study_field: StudyField;
  study_goal: StudyGoal;
  study_level: StudyLevel;
  language: string;
  onboarded_at: string | null;
  is_onboarded: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  profile: LearnerProfile;
}

export interface AuthTokenResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_at: string;
  refresh_expires_at: string;
  session_id: string;
}

export interface AtcCode {
  code: string;
  name: string;
  level: number;
  ingredient_count?: number;
}

export interface IngredientListItem {
  rxcui: string;
  name: string;
  slug: string;
  n_products: number;
  n_source_records: number;
  pharm_classes: string[];
  atc_codes: AtcCode[];
}

export type SectionTone = "info" | "deny" | "boxed" | "caution" | "special";

export interface ProfileSection {
  field: string;
  label: string;
  has_content: boolean;
  has_summary: boolean;
  n_contributing_products: number;
  summary_fa: string;
  summary_en: string;
  raw_text: string;
}

export interface LessonSection {
  key: string;
  field: string;
  title_fa: string;
  title_en: string;
  tone: SectionTone;
  text_fa: string;
  text_en: string;
  has_summary: boolean;
}

export interface IngredientDetail extends IngredientListItem {
  sections: ProfileSection[];
  lesson_sections: LessonSection[];
}

export interface Subgroup {
  code: string;
  name_fa: string;
  name_en: string;
  total: number;
  done: number;
}

export interface LessonGroup {
  code: string;
  name_fa: string;
  name_en: string;
  subgroups: Subgroup[];
}

export interface ExamPoint {
  drug_name: string;
  drug_slug: string;
  field: string;
  tone: SectionTone;
  point_fa: string;
  point_en: string;
}

export interface ChapterProgress {
  read_drug_slugs: string[];
  scroll_pct: number;
  last_opened_at: string;
}

export interface Chapter {
  code: string;
  name_fa: string;
  name_en: string;
  group_code: string;
  group_name_fa: string;
  group_name_en: string;
  drugs: IngredientDetail[];
  exam_points: ExamPoint[];
  progress: ChapterProgress;
}

export type FocusRowKind = "leitner" | "mistake" | "lesson";

export interface FocusRow {
  kind: FocusRowKind;
  title_fa: string;
  title_en: string;
  sub_fa: string;
  sub_en: string;
  minutes: number;
  count?: number;
  mistake_id?: number;
  atc_code?: string;
}

export interface NextChapter {
  code: string;
  name_fa: string;
  name_en: string;
  group_code: string;
  group_name_fa: string;
  group_name_en: string;
}

export interface Dashboard {
  greeting_name: string;
  streak_days: number;
  xp: number;
  next_chapter: NextChapter | null;
  focus_session: { rows: FocusRow[]; total_minutes: number };
}

export interface Statistics {
  week_bars: number[];
  accuracy_pct: number;
  quizzes: number;
  reviews: number;
  minutes: number;
  mastery_pct: number;
}

export interface Mistake {
  id: number;
  topic_key: string;
  topic_fa: string;
  topic_en: string;
  detail_fa: string;
  detail_en: string;
  count: number;
  resolved: boolean;
  last_seen: string;
}

export interface StudyPlan {
  days: boolean[];
  reminders_enabled: boolean;
  updated_at?: string;
}

export interface LeitnerCard {
  id: number;
  drug_slug: string;
  box: number;
  due_at: string;
  times_seen: number;
  front_fa: string;
  front_en: string;
  back_fa: string;
  back_en: string;
}

export interface BoxSummary {
  box: number;
  count: number;
  due: number;
  next_due_at: string | null;
}

export interface QuizQuestion {
  id: number;
  order: number;
  prompt_fa: string;
  prompt_en: string;
  options_fa: string[];
  options_en: string[];
}

export interface QuizSession {
  id: number;
  category: string;
  question_count: number;
  questions: QuizQuestion[];
}

export interface QuizAnswerResult {
  correct: boolean;
  correct_index: number;
}

export interface QuizResult {
  score: number;
  total: number;
  mistakes_added: number;
}

export interface UptodateTopic {
  id: string;
  title: string;
  section: string;
  version: string;
}

export interface UptodateArticle extends UptodateTopic {
  contributors: string[];
  outline_html: string;
  body_html: string;
}
