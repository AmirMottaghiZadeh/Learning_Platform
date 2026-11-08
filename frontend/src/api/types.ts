/** Response shapes — mirror `docs/05-api.md`. */

export type StudyField = "" | "pharmacy" | "medicine" | "nursing";
export type StudyGoal = "" | "comprehensive" | "residency" | "final" | "clinical";
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
  /** verified mobile number ("09xxxxxxxxx"), null for email-only accounts */
  phone: string | null;
  /** false right after an SMS sign-up, until a password is chosen */
  has_password: boolean;
  /** a throwaway account made while guest access is on: no sign-in screens */
  is_guest?: boolean;
  first_name: string;
  last_name: string;
  roles: string[];
  profile: LearnerProfile;
}

export type OtpPurpose = "signup" | "reset";

export interface OtpRequestResponse {
  phone: string;
  code_length: number;
  expires_in: number;
  resend_in: number;
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
  is_reviewed?: boolean;
  rxcui: string;
  name: string;
  slug: string;
  n_products: number;
  n_source_records: number;
  pharm_classes: string[];
  atc_codes: AtcCode[];
}

export type SectionTone = "info" | "deny" | "boxed" | "caution" | "special";

/** Per-field flags for a drug's lesson; the text itself is in
 * `lesson_sections`. */
export interface LessonDrugSection {
  field: string;
  label: string;
  has_summary: boolean;
}

export interface LessonSection {
  key: string;
  field: string;
  title_fa: string;
  title_en: string;
  tone: SectionTone;
  text_fa: string;
  text_en: string;
  other_sources_fa?: string;
  other_sources_en?: string;
  has_summary: boolean;
}

/** One drug's lesson -- GET /lessons/drugs/<slug>/, fetched when it's opened. */
export interface LessonDrug extends IngredientListItem {
  sections: LessonDrugSection[];
  lesson_sections: LessonSection[];
}

/** The ATC level-4 class (N04BC) a drug is listed under within its chapter. */
export interface AtcGroup {
  code: string;
  /** blank when no Persian name is known */
  name_fa: string;
  name_en: string;
}

/** A chapter's drug list entry: names only, the lesson comes per drug. */
export interface ChapterDrug {
  is_reviewed?: boolean;
  slug: string;
  name: string;
  name_fa?: string;
  pharm_classes: string[];
  /** drugs arrive ordered by it, so each group is one contiguous run */
  atc_group: AtcGroup | null;
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
  /** The broad body-system/domain this study topic sits under — purely for
   * clustering the 50+ topics into a shorter list to pick from first. */
  category_code: string;
  category_name_fa: string;
  category_name_en: string;
  subgroups: Subgroup[];
}

export interface ChapterProgress {
  read_drug_slugs: string[];
  scroll_pct: number;
  last_opened_at: string;
}

export interface LessonTopic {
  code: string;
  name_fa: string;
  name_en: string;
}

export interface Chapter {
  code: string;
  name_fa: string;
  name_en: string;
  /** The chapter's primary study topic (see LessonTopic) — kept under these
   * field names for backward compatibility. */
  group_code: string;
  group_name_fa: string;
  group_name_en: string;
  /** Every study topic this chapter belongs to (usually 1; a drug class
   * that's first-line across several indications lists more than one). */
  topics: LessonTopic[];
  /** The true, unmodified ATC anatomical (L1) group name, for rigour. */
  anatomical_name_fa: string;
  anatomical_name_en: string;
  drugs: ChapterDrug[];
  progress: ChapterProgress;
}

export type FocusRowKind = "mistake" | "lesson";

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

/** The terms or the privacy page of the site (GET /app/legal/<slug>/). */
export interface LegalPage {
  title: string;
  body_html: string;
  updated_at: string;
}

/** One of the learner's active plans or products (GET /billing/me/). */
export interface MyEntitlement {
  id: number;
  plan_name_fa: string;
  plan_kind: "plan" | "product";
  /** "purchase", "admin", or "trial" (the month given at sign-up). */
  source: string;
  starts_at: string;
  /** Null: permanent. */
  ends_at: string | null;
  days_left: number | null;
}

export interface MyAccess {
  enforced: boolean;
  entitlements: MyEntitlement[];
}

// --- buying (GET /billing/catalog/, POST /billing/quote/ and /checkout/) ---

export interface PlanPrice {
  id: number;
  /** null: permanent */
  duration_days: number | null;
  /** "۳ ماه", "دائمی" */
  duration_label: string;
  price_toman: number;
  /** the price before the offer, shown struck through */
  compare_at_toman: number | null;
  label_fa: string;
}

export interface PlanFeatureItem {
  key: string;
  name_fa: string;
  /** how the plan words it ("" = name_fa, with the limit) */
  label_fa: string;
  /** whether the plan's card lists it */
  is_listed: boolean;
  limit: number | null;
  period: string;
  /** "در ماه"; "" without a limit */
  period_fa?: string;
  unit_fa: string;
}

export interface CatalogPlan {
  id: number;
  kind: "plan" | "product";
  slug: string;
  name_fa: string;
  name_en: string;
  tagline_fa: string;
  description_fa: string;
  badge_fa: string;
  cta_label_fa: string;
  extra_lines: string[];
  is_free: boolean;
  prices: PlanPrice[];
  features: PlanFeatureItem[];
}

export interface Catalog {
  free: CatalogPlan | null;
  plans: CatalogPlan[];
  products: CatalogPlan[];
  gateways?: { kind: string; name: string }[];
  sales_enabled?: boolean;
}

export interface PriceQuote {
  amount_toman: number;
  discount_toman: number;
  payable_toman: number;
}

export interface CheckoutResult {
  order_id: number;
  status: "pending" | "paid" | "failed" | "canceled";
  /** the site's page that takes the buyer to the gateway; "" when nothing was left to pay */
  payment_url: string;
}

export interface BillingOrder {
  id: number;
  plan_name_fa: string;
  duration_days: number | null;
  amount_toman: number;
  discount_toman: number;
  payable_toman: number;
  status: "pending" | "paid" | "failed" | "canceled";
  ref_id: string;
  created_at: string;
  paid_at: string | null;
  error?: string;
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

export type PlanMode = "none" | "goal" | "maintenance";

export interface StudyPlan {
  mode: PlanMode;
  topic_keys: string[];
  daily_minutes: number;
  deadline: string | null;
  days: boolean[];
  reminders_enabled: boolean;
  updated_at?: string;
  /** Present only on the PUT response: whether the newly generated goal-mode
   * schedule fits before the deadline at this daily_minutes (always true for
   * the other two modes). */
  fits_deadline?: boolean;
}

export type PlanItemActivity = "lesson" | "quiz" | "mistake_review";
export type PlanItemStatus = "pending" | "done" | "skipped";

export interface StudyPlanItem {
  id: number;
  day: string;
  order: number;
  activity_type: PlanItemActivity;
  topic_key: string;
  atc_code: string;
  estimated_minutes: number;
  status: PlanItemStatus;
  reason_fa: string;
  reason_en: string;
  completed_at: string | null;
  /** What the task is ("دارونامه: ضدفشارخون‌ها"). */
  title_fa: string;
  title_en: string;
}

/** The line above the Today box. The day and week counts are null outside
 * a goal plan with an exam date. */
export interface PlanSummary {
  daily_minutes: number;
  study_days: number;
  deadline: string | null;
  days_left: number | null;
  week_index: number | null;
  week_count: number | null;
  progress_pct: number | null;
}

export type PlanDayState = "done" | "missed" | "today" | "planned" | "free" | "off";

/** One day of this week, Saturday first. */
export interface PlanDay {
  date: string;
  study_day: boolean;
  state: PlanDayState;
}

export interface PlanTopicStatus {
  key: string;
  name_fa: string;
  name_en: string;
  progress_pct: number;
  mastery_pct: number;
}

export interface PlanToday {
  mode: PlanMode;
  items: StudyPlanItem[];
  total_minutes: number;
  /** Empty when asked for briefly (the home screen). */
  topics: PlanTopicStatus[];
  summary: PlanSummary;
  week: PlanDay[];
}

export interface QuizQuestion {
  id: number;
  order: number;
  prompt_fa: string;
  prompt_en: string;
  options_fa: string[];
  options_en: string[];
  field: string;
  field_label_fa: string;
  field_tone: SectionTone;
  subject_slug: string;
}

export interface QuizSession {
  id: number;
  category: string;
  atc_code: string;
  question_count: number;
  questions: QuizQuestion[];
}

export interface QuizAnswerResult {
  correct: boolean;
  correct_index: number;
  extra_context: string[];
}

export interface QuizFieldBreakdown {
  field: string;
  label_fa: string;
  tone: SectionTone;
  correct: number;
  total: number;
}

export interface QuizMissedQuestion {
  prompt_fa: string;
  options_fa: string[];
  correct_index: number;
  selected_index: number;
}

export interface QuizResult {
  score: number;
  total: number;
  mistakes_added: number;
  by_field: QuizFieldBreakdown[];
  missed: QuizMissedQuestion[];
  previous_best_pct: number | null;
}

export interface QuizOverview {
  avg_score_pct: number;
  total_quizzes: number;
  weak_topics_count: number;
  mastery: Record<string, number>;
}

export interface QuizFieldPreview {
  field: string;
  label_fa: string;
  tone: SectionTone;
  count: number;
}

export interface QuizPreview {
  available: number;
  estimated_minutes: number;
  by_field: QuizFieldPreview[];
}

export interface UptodateTopic {
  id: string;
  title: string;
  section: string;
  sections?: string[];
  version: string;
  /** the topic's own "last updated" date ("Feb 11, 2026"), or "" */
  updated: string;
}

export interface UptodateSearchResult extends UptodateTopic {
  /** always empty: snippets are not returned */
  snippet: string;
  /** the title-word starts the query was matched with, to highlight */
  terms?: string[];
  /** the query with its misspelt words corrected; "" when none was */
  corrected?: string;
}

export type UptodateSuggestionKind = "general" | "treatment" | "diagnosis" | "followup";

export interface UptodateSearchSuggestion {
  query: string;
  label: string;
  /** Optional while older API responses remain in caches. */
  kind?: UptodateSuggestionKind;
  /** Distinct valid articles associated with this concept, before section filtering. */
  count?: number;
}

/** One page of the topic search (`paged=1`). */
export interface UptodateSearchPage {
  /** every match (in the section asked for, if one was), not just this page */
  total: number;
  /** every match, whatever section was asked for */
  all: number;
  /** every match per section, busiest first, whatever section was asked for */
  sections: { name: string; count: number }[];
  terms: string[];
  corrected: string;
  suggestions?: UptodateSearchSuggestion[];
  results: UptodateSearchResult[];
}

export interface UptodateArticle extends UptodateTopic {
  /** Set only by the local Medscape adapter, not by the UpToDate API. */
  reference_kind?: MedscapeKind;
  contributors: string[];
  outline_html: string;
  body_html: string;
  search_anchor_status?: "matched" | "missing" | "stale";
}

export interface UptodateImage {
  id: string;
  content_type: string;
  data_base64: string;
}

export type LexicompDrugKind = "generic" | "brand";

export interface LexicompDrug {
  id: number;
  name: string;
  generic_id: number;
  kind: LexicompDrugKind;
}

export interface LexicompInteraction {
  monograph_id: number;
  drug_ids: number[];
  object_generic_id: number;
  object_name: string;
  precipitant_generic_id: number;
  precipitant_name: string;
  severity: string;
  reliability: string;
  summary: string;
  management: string;
  discussion: string;
  footnotes: string;
}

export type CalculatorQuestionType = "multiple_choice" | "numeric_input" | "date_input" | "days_input";

export interface CalculatorChoice {
  title_primary: string;
  title_primary_fa: string;
  title_secondary: string | null;
  title_secondary_fa: string | null;
  answer_factor: string | null;
}

export interface CalculatorUnit {
  title: string;
  title_fa: string;
  min_value: string | null;
  max_value: string | null;
  min_value_msg: string | null;
  min_value_msg_fa: string | null;
  max_value_msg: string | null;
  max_value_msg_fa: string | null;
  unit_factor: string | null;
  initial_value: string | null;
}

export interface CalculatorQuestion {
  position: number;
  title: string;
  title_fa: string;
  type: CalculatorQuestionType;
  more_information: string | null;
  more_information_fa: string | null;
  section_name: string | null;
  section_name_fa: string | null;
  initial_value: string | null;
  choices: CalculatorChoice[];
  units: CalculatorUnit[];
}

export interface CalculatorResultDef {
  position: number;
  title: string;
  title_fa: string;
  title_formula: string | null;
  sub_title: string | null;
  sub_title_fa: string | null;
  sub_title_formula: string | null;
  formula: string | null;
  condition_formula: string | null;
  answer: string | null;
  answer_fa: string | null;
  type: string | null;
}

export interface CalculatorErrorCheck {
  position: number;
  type: string | null;
  title: string;
  title_fa: string;
  answer: string | null;
  answer_fa: string | null;
  formula: string | null;
}

export interface CalculatorReference {
  names: string | null;
  sources: string | null;
  papers: string | null;
}

export interface CalculatorCategoryRef {
  id: number;
  name: string;
  name_fa: string;
  parent_id: number | null;
  is_main_category: boolean;
}

export interface CalculatorTagRef {
  id: number;
  name: string;
  name_fa: string;
}

export interface CalculatorListItem {
  slug: string;
  name: string;
  name_fa: string;
  description: string;
  description_fa: string;
  categories: CalculatorCategoryRef[];
}

export interface CalculatorDetail extends CalculatorListItem {
  tags: CalculatorTagRef[];
  url: string;
  about: string;
  about_fa: string;
  disclaimer_footer: string;
  disclaimer_footer_fa: string;
  questions: CalculatorQuestion[];
  results: CalculatorResultDef[];
  error_checks: CalculatorErrorCheck[];
  /** English text a result formula returns literally -> Persian. */
  formula_strings_fa: Record<string, string>;
  references: CalculatorReference[];
}

export type MedscapeKind = "disease" | "guideline";

export interface MedscapeCategoryNode {
  category: string;
  specialties: { name: string; count: number }[];
}

export interface MedscapeArticleListItem {
  slug: string;
  title: string;
  kind: MedscapeKind;
  latest_update: string | null;
}

export type MedscapeBlock =
  | { type: "paragraph"; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "table"; headers: string[] | null; rows: string[][] }
  | { type: "image"; id: number; alt: string; caption: string };

export interface MedscapeSection {
  heading: string;
  blocks: MedscapeBlock[];
  children: MedscapeSection[];
}

export interface MedscapeImage {
  id: number;
  content_type: string;
  data_base64: string;
}

export interface MedscapeArticleDetail extends MedscapeArticleListItem {
  meta: string;
  url: string;
  categories: { category: string; specialty: string }[];
  sections: MedscapeSection[];
}

/** One hit of the lessons' drug search (GET /lessons/search/?q=). */
export interface LessonDrugSearchResult {
  is_reviewed?: boolean;
  slug: string;
  name: string;
  name_fa: string;
  /** the lesson chapters the drug appears in; the first opens it */
  chapters: { code: string; name_fa: string; name_en: string }[];
}

// --- offline reference packages (GET /offline/packages/) ---------------

export type OfflineDataset = "uptodate" | "lexicomp";

export interface OfflinePackageFile {
  name: string;
  size: number;
  sha256: string;
  md5: string;
}

/** A built package as published in the bucket (its latest.json). */
export interface OfflineManifest {
  format: number;
  dataset: OfflineDataset;
  build: string;
  source_version: string;
  created_at: string;
  files: OfflinePackageFile[];
  total_size: number;
  /** [part, offset, length] of the sealed index record */
  index: [number, number, number];
  /** hex of a sealed known plaintext, to tell a wrong key from bad data */
  check: string;
}

export interface OfflinePackageInfo {
  dataset: OfflineDataset;
  /** whether this learner's plan lets them keep it offline */
  entitled: boolean;
  license_days: number;
  /** null until something is published */
  package: OfflineManifest | null;
}

export interface OfflinePackageUrls {
  build: string;
  expires_at: string;
  files: (OfflinePackageFile & { url: string })[];
}

export interface OfflineLicense {
  build: string;
  server_time: string;
  valid_until: string;
  /** base64 raw AES key (native app) */
  key?: string;
  /** base64 key wrapped with RSA-OAEP to the browser's key (web) */
  wrapped_key?: string;
}

// GET /app/release/: whether this install should update (backend
// apps.website.api, from the releases entered in the site panel).
export type AppReleaseInfo = {
  version: string;
  version_code: number;
  notes: string[];
  released_at: string;
  download_url: string;
};
export type ReleaseCheck = {
  update: "none" | "optional" | "required";
  latest: AppReleaseInfo | null;
};

// --- announcements from the admin (backend apps.announcements) ------------

export type AnnouncementKind = "news" | "update" | "warning" | "offer";

export type AnnouncementButton = {
  label: string;
  /** "url": open `url`; "app": navigate; "pwa": request browser installation */
  kind: "url" | "app" | "pwa";
  url: string;
  screen: string;
  param: string;
};

export type AppAnnouncement = {
  id: number;
  title: string;
  body: string;
  kind: AnnouncementKind;
  kind_label: string;
  button: AnnouncementButton | null;
  dismissible: boolean;
  pinned: boolean;
  /** false until this app reported it shown: an unseen one opens dimmed */
  seen: boolean;
  starts_at: string;
  /** a draft the admin sent to their own phone */
  is_test: boolean;
};

export type AnnouncementEvent = "seen" | "click" | "dismiss";
