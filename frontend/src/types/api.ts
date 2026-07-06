export type User = {
  id: number;
  username: string;
  email: string;
};

export type AuthResponse = {
  user: User;
  token: string;
};

export type Topic = {
  key: string;
  label: string;
  detail: string;
};

export type TargetCategory = {
  key: string;
  label: string;
  count: number;
};

export type QuestionType = "brandGeneric" | "timing" | "indication" | "sideEffects";

export type WeakTopic = {
  topic_key: string;
  topic_label: string;
  questions_answered: number;
  accuracy_percent: number;
  wrong_answers: number;
  review_count: number;
  mistake_count: number;
  due_flashcards: number;
  xp: number;
  mastery_state: string;
};

export type ProgressSummary = {
  product_id: string | null;
  questions_answered: number;
  correct_answers: number;
  accuracy_percent: number;
  xp: number;
  review_count: number;
  mistake_count: number;
  due_flashcards: number;
  active_flashcards: number;
  current_streak: number;
  weak_topics: WeakTopic[];
};

export type Recommendation = {
  id: string;
  priority: number;
  action: string;
  title: string;
  reason: string;
  topic_key: string | null;
  count: number;
};

export type LeagueSummary = {
  season_key: string;
  rank: number | null;
  total_participants: number;
};

export type Dashboard = {
  product_id: string;
  summary: ProgressSummary;
  recommendations: Recommendation[];
  league: LeagueSummary;
};

export type TopicProgress = {
  id: number;
  product_id: string;
  topic_key: string;
  topic_label: string;
  questions_answered: number;
  correct_answers: number;
  wrong_answers: number;
  timed_out_answers: number;
  accuracy_percent: number;
  xp: number;
  review_count: number;
  mistake_count: number;
  mastery_state: string;
  last_activity_at: string | null;
};

export type DailyActivity = {
  date: string;
  questions_answered: number;
  reviews_completed: number;
  mistakes_created: number;
  xp: number;
};

export type Statistics = {
  product_id: string;
  days: number;
  start_date: string;
  end_date: string;
  summary: ProgressSummary;
  topics: TopicProgress[];
  daily_activity: DailyActivity[];
  weak_topics: WeakTopic[];
};

export type GameQuestion = {
  id: number;
  order: number;
  question_type: string;
  interaction_type: "binary" | "segmented" | "multiple_choice";
  option_layout: "compact" | "list";
  instruction: string;
  prompt: string;
  subtitle: string;
  chip: string;
  options: string[];
  timer_base_seconds: number;
  timer_extension_seconds: number;
  timer_total_seconds: number;
  timer_remaining_seconds: number;
  timer_extension_used: boolean;
  timer_extension_available: boolean;
};

export type GameSession = {
  id: number;
  topic_key: string;
  target_category_key: string;
  mode: "random" | "category" | "all" | "mistakes" | "league";
  total_questions: number;
  timer_seconds: number;
  score: number;
  correct_count: number;
  streak: number;
  status: "active" | "paused" | "finished" | "archived";
  paused_at: string | null;
  total_paused_seconds: number;
  is_finished: boolean;
  current_question: GameQuestion | null;
};

export type GameAnswer = {
  id: number;
  is_correct: boolean;
  time_expired: boolean;
  correct_answer: string;
  remaining_seconds: number;
  score_delta: number;
  xp_delta: number;
  scoring_rule_version: string;
};

export type GameAnswerResult = {
  answer: GameAnswer;
  game: GameSession;
};

export type Mistake = {
  id: number;
  topic_key: string;
  prompt: string;
  correct_answer: string;
  feedback: string;
  wrong_count: number;
  last_wrong_answer: string;
  last_at: string;
};

export type FlashcardState = {
  id: number;
  prompt: string;
  correct_answer: string;
  feedback: string;
  source_type: string;
  target_category_key: string;
  target_category_label: string;
  is_in_leitner_box: boolean;
  box: number;
  review_state: string;
  interval_days: number;
  review_count: number;
  lapse_count: number;
  last_rating: string;
  schedule_rule_version: string;
  due_at: string | null;
  last_reviewed_at: string | null;
};

export type FlashcardBox = {
  box: number;
  count: number;
};

export type FlashcardBoxSummary = {
  new: number;
  boxes: FlashcardBox[];
};

export type FlashcardDeckSummary = {
  product_id: string;
  target_category_key: string;
  source_type: string;
  eligible_sources: number;
  scheduled_cards: number;
  unscheduled_sources: number;
  active_cards: number;
  due_cards: number;
  leitner: FlashcardBoxSummary;
};

export type LeagueSeason = {
  id: number;
  product_id: string;
  key: string;
  starts_at: string;
  ends_at: string;
  status: string;
};

export type LeagueResult = {
  id: number;
  username: string;
  product_id: string;
  season: LeagueSeason | null;
  season_key: string;
  topic_key: string;
  raw_score: number;
  score_per_question: string;
  time_bonus: string;
  league_rating: string;
  answered: number;
  correct: number;
  wrong: number;
  percent: number;
  duration_seconds: number;
  rank_snapshot: number | null;
  league_rule_version: string;
  created_at: string;
};

export type LeaderboardEntry = {
  rank: number;
  result: LeagueResult;
};

export type MyLeagueRank = {
  rank: number | null;
  result: LeagueResult | null;
  total_participants: number;
};

export type LeagueFullSummary = {
  season: LeagueSeason | null;
  season_key: string;
  topic_key: string;
  leaderboard: LeaderboardEntry[];
  my_rank: MyLeagueRank;
  total_participants: number;
  rule_version: string;
};
