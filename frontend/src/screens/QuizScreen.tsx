import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {useCallback, useEffect, useRef, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {Bookmark, CheckCircle2, Clock3, PlayCircle, RotateCcw, Send, Square, TimerReset, Trash2} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {
  EmptyState,
  ErrorState,
  LearningCard,
  LoadingState,
  PrimaryButton,
  ScreenContainer,
  ScreenHeader,
  SecondaryButton,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {GameAnswer, GameQuestion, GameSession, QuestionType, TargetCategory} from "../types/api";

const GAME_COUNTS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
const QUESTION_TYPES: Array<{key: QuestionType; label: string}> = [
  {key: "brandGeneric", label: "نام تجاری"},
  {key: "timing", label: "با غذا / بی غذا"},
  {key: "sideEffects", label: "عوارض"},
  {key: "indication", label: "اندیکاسیون"},
];

const SAVED_QUIZ_SESSION_KEY = "k_game_saved_quiz_session";
const DEFAULT_QUESTION_SECONDS = 30;
const TIMER_EXTENSION_SECONDS = 30;

type SavedQuizSession = {
  id: number;
  userId: number | null;
  questionType: QuestionType;
  mode: "random" | "category";
  count: number;
  targetCategoryKey: string;
  score: number;
  correctCount: number;
  savedAt: string;
};

function isQuestionType(value: string): value is QuestionType {
  return QUESTION_TYPES.some((type) => type.key === value);
}

export function QuizScreen() {
  const {token, user} = useAuth();
  const [categories, setCategories] = useState<TargetCategory[]>([]);
  const [selectedQuestionType, setSelectedQuestionType] = useState<QuestionType>("brandGeneric");
  const [selectedMode, setSelectedMode] = useState<"random" | "category">("random");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedCount, setSelectedCount] = useState(10);
  const [session, setSession] = useState<GameSession | null>(null);
  const [savedSession, setSavedSession] = useState<SavedQuizSession | null>(null);
  const [answer, setAnswer] = useState<GameAnswer | null>(null);
  const [answeredQuestion, setAnsweredQuestion] = useState<GameQuestion | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(DEFAULT_QUESTION_SECONDS);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const categoryRequestRef = useRef(0);

  const resetCurrentQuiz = useCallback(() => {
    setSession(null);
    setAnswer(null);
    setAnsweredQuestion(null);
    setRemainingSeconds(DEFAULT_QUESTION_SECONDS);
  }, []);

  const loadCategories = useCallback(async () => {
    if (!token) return;
    const requestId = categoryRequestRef.current + 1;
    categoryRequestRef.current = requestId;
    setLoading(true);
    setError(null);
    try {
      const payload = await platformApi.targetCategories(token, selectedQuestionType);
      if (requestId !== categoryRequestRef.current) return;
      setCategories(payload);
      if (!payload.some((category) => category.key === selectedCategory)) {
        setSelectedCategory(payload[0]?.key ?? "");
      } else if (payload[0]?.key && !selectedCategory) {
        setSelectedCategory(payload[0].key);
      }
    } catch (exc) {
      if (requestId !== categoryRequestRef.current) return;
      setError(exc instanceof Error ? exc.message : "Categories unavailable.");
    } finally {
      if (requestId === categoryRequestRef.current) setLoading(false);
    }
  }, [selectedCategory, selectedQuestionType, token]);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    let active = true;
    async function loadSavedSession() {
      try {
        const raw = await AsyncStorage.getItem(SAVED_QUIZ_SESSION_KEY);
        if (!raw) {
          if (active) setSavedSession(null);
          return;
        }
        const parsed = JSON.parse(raw) as SavedQuizSession;
        if (parsed.userId && user?.id && parsed.userId !== user.id) {
          if (active) setSavedSession(null);
          return;
        }
        if (active) setSavedSession(parsed);
      } catch {
        await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
        if (active) setSavedSession(null);
      }
    }
    loadSavedSession();
    return () => {
      active = false;
    };
  }, [user?.id]);

  useEffect(() => {
    const currentQuestion = session?.current_question;
    if (!currentQuestion) {
      setRemainingSeconds(DEFAULT_QUESTION_SECONDS);
      return;
    }
    setRemainingSeconds(currentQuestion.timer_remaining_seconds ?? session.timer_seconds ?? DEFAULT_QUESTION_SECONDS);
  }, [session?.current_question?.id, session?.current_question?.timer_remaining_seconds, session?.timer_seconds]);

  useEffect(() => {
    if (!session?.current_question || answer || session.status !== "active") return;
    const interval = setInterval(() => {
      setRemainingSeconds((value) => Math.max(0, value - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [answer, session?.current_question?.id, session?.status]);

  function resetSelectionQuestions() {
    categoryRequestRef.current += 1;
    resetCurrentQuiz();
    setCategories([]);
    setError(null);
    setLoading(true);
  }

  function chooseQuestionType(questionType: QuestionType) {
    if (questionType === selectedQuestionType) return;
    resetSelectionQuestions();
    setSelectedQuestionType(questionType);
    setSelectedCategory("");
  }

  function chooseMode(mode: "random" | "category") {
    if (mode === selectedMode) return;
    resetCurrentQuiz();
    setAnswer(null);
    setAnsweredQuestion(null);
    setSelectedMode(mode);
  }

  function chooseCount(count: number) {
    if (count === selectedCount) return;
    resetCurrentQuiz();
    setAnswer(null);
    setAnsweredQuestion(null);
    setSelectedCount(count);
  }

  function chooseCategory(categoryKey: string) {
    if (categoryKey === selectedCategory) return;
    resetCurrentQuiz();
    setAnswer(null);
    setAnsweredQuestion(null);
    setSelectedCategory(categoryKey);
  }

  async function saveCurrentQuizForLater() {
    if (!token || !session) return;
    setBusy(true);
    setError(null);
    try {
      const paused = await platformApi.pauseGame(token, session.id);
      const questionType = isQuestionType(paused.topic_key) ? paused.topic_key : selectedQuestionType;
      const payload: SavedQuizSession = {
        id: paused.id,
        userId: user?.id ?? null,
        questionType,
        mode: paused.mode === "category" ? "category" : "random",
        count: paused.total_questions,
        targetCategoryKey: paused.target_category_key,
        score: paused.score,
        correctCount: paused.correct_count,
        savedAt: new Date().toISOString(),
      };
      await AsyncStorage.setItem(SAVED_QUIZ_SESSION_KEY, JSON.stringify(payload));
      setSavedSession(payload);
      resetCurrentQuiz();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not save quiz.");
    } finally {
      setBusy(false);
    }
  }

  async function resumeSavedQuiz() {
    if (!token || !savedSession) return;
    setBusy(true);
    setError(null);
    setAnswer(null);
    setAnsweredQuestion(null);
    try {
      const resumed = await platformApi.resumeGame(token, savedSession.id);
      const questionType = isQuestionType(resumed.topic_key) ? resumed.topic_key : savedSession.questionType;
      setSelectedQuestionType(questionType);
      setSelectedMode(resumed.mode === "category" ? "category" : "random");
      setSelectedCount(resumed.total_questions || savedSession.count);
      setSelectedCategory(resumed.target_category_key || savedSession.targetCategoryKey);
      setSession(resumed);
      await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
      setSavedSession(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not resume saved quiz.");
    } finally {
      setBusy(false);
    }
  }

  async function discardSavedQuiz() {
    await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
    setSavedSession(null);
  }

  async function start() {
    if (!token) return;
    if (selectedMode === "category" && !selectedCategory) {
      setError("Select a category first.");
      return;
    }
    setBusy(true);
    setError(null);
    setAnswer(null);
    setAnsweredQuestion(null);
    try {
      setSession(
        await platformApi.startGame(
          token,
          selectedQuestionType,
          selectedMode,
          selectedCount,
          selectedMode === "category" ? selectedCategory : "",
        ),
      );
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not start quiz.");
    } finally {
      setBusy(false);
    }
  }

  async function extendTimer() {
    if (!token || !session?.current_question) return;
    setBusy(true);
    setError(null);
    try {
      const updatedSession = await platformApi.extendGameTimer(token, session.id);
      setSession(updatedSession);
      setAnswer(null);
      setAnsweredQuestion(null);
      const updatedQuestion = updatedSession.current_question;
      if (updatedQuestion) {
        setRemainingSeconds(updatedQuestion.timer_remaining_seconds);
      }
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not extend timer.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(selected_answer: string) {
    if (!token || !session?.current_question) return;
    setBusy(true);
    setError(null);
    try {
      const currentQuestion = session.current_question;
      const result = await platformApi.answerQuestion(
        token,
        session.id,
        currentQuestion.id,
        selected_answer,
      );
      setAnswer(result.answer);
      setAnsweredQuestion(currentQuestion);
      setSession(result.game);
      setRemainingSeconds(result.answer.remaining_seconds);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Answer failed.");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    if (!token || !session) return;
    setBusy(true);
    try {
      setSession(await platformApi.finishGame(token, session.id));
      setAnswer(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Finish failed.");
    } finally {
      setBusy(false);
    }
  }

  const question = session?.current_question ?? null;
  const timerTotalSeconds = question?.timer_total_seconds ?? session?.timer_seconds ?? DEFAULT_QUESTION_SECONDS;
  const timerPercent = timerTotalSeconds ? (remainingSeconds / timerTotalSeconds) * 100 : 0;
  const canExtendTimer = Boolean(question?.timer_extension_available && !answer && !busy);
  const timerStatus = remainingSeconds <= 0 ? "تمام شد" : `${remainingSeconds}s`;

  if (loading && !session) return <LoadingState label="Loading quiz" />;

  return (
    <ScreenContainer>
      <ScreenHeader eyebrow="Focused practice" title="Quiz" />
      {error ? <ErrorState message={error} onRetry={loadCategories} /> : null}

      {!session ? (
        <>
          {savedSession ? (
            <LearningCard tone="amber">
              <View style={styles.savedTop}>
                <View>
                  <Text style={styles.label}>روند ذخیره‌شده</Text>
                  <Text style={styles.savedMeta}>
                    {QUESTION_TYPES.find((type) => type.key === savedSession.questionType)?.label ?? savedSession.questionType}
                    {" · "}
                    {savedSession.mode === "category" ? "Category" : "Random"}
                    {" · "}
                    Score {savedSession.score}
                  </Text>
                </View>
              </View>
              <View style={styles.actionGrid}>
                <PrimaryButton label="ادامه" Icon={RotateCcw} onPress={resumeSavedQuiz} disabled={busy} />
                <SecondaryButton label="حذف" Icon={Trash2} onPress={discardSavedQuiz} disabled={busy} />
              </View>
            </LearningCard>
          ) : null}
          <LearningCard tone="lavender">
            <Text style={styles.label}>نوع سؤال</Text>
            <View style={styles.topicWrap}>
              {QUESTION_TYPES.map((type) => (
                <Pressable
                  key={type.key}
                  accessibilityRole="button"
                  onPress={() => chooseQuestionType(type.key)}
                  style={[styles.topicChip, selectedQuestionType === type.key && styles.topicChipActive]}
                >
                  <Text style={[styles.topicText, selectedQuestionType === type.key && styles.topicTextActive]}>
                    {type.label}
                  </Text>
                </Pressable>
              ))}
            </View>
          </LearningCard>
          <LearningCard tone="mint">
            <Text style={styles.label}>Mode</Text>
            <View style={styles.topicWrap}>
              {(["random", "category"] as const).map((mode) => (
                <Pressable
                  key={mode}
                  accessibilityRole="button"
                  onPress={() => chooseMode(mode)}
                  style={[styles.topicChip, selectedMode === mode && styles.topicChipActive]}
                >
                  <Text style={[styles.topicText, selectedMode === mode && styles.topicTextActive]}>
                    {mode === "random" ? "Random" : "Category"}
                  </Text>
                </Pressable>
              ))}
            </View>
          </LearningCard>
          <LearningCard tone="blue">
            <Text style={styles.label}>Questions</Text>
            <View style={styles.topicWrap}>
              {GAME_COUNTS.map((count) => (
                <Pressable
                  key={count}
                  accessibilityRole="button"
                  onPress={() => chooseCount(count)}
                  style={[styles.countChip, selectedCount === count && styles.topicChipActive]}
                >
                  <Text style={[styles.topicText, selectedCount === count && styles.topicTextActive]}>
                    {count}
                  </Text>
                </Pressable>
              ))}
            </View>
          </LearningCard>
          {selectedMode === "category" ? (
            <LearningCard tone="sage">
              <Text style={styles.label}>Category</Text>
              <View style={styles.topicWrap}>
                {categories.map((category) => (
                  <Pressable
                    key={category.key}
                    accessibilityRole="button"
                    onPress={() => chooseCategory(category.key)}
                    style={[styles.topicChip, selectedCategory === category.key && styles.topicChipActive]}
                  >
                    <Text style={[styles.topicText, selectedCategory === category.key && styles.topicTextActive]}>
                      {category.label} · {category.count}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </LearningCard>
          ) : null}
          <PrimaryButton label="Start quiz" Icon={PlayCircle} onPress={start} disabled={busy} />
        </>
      ) : (
        <>
          <LearningCard tone="lavender">
            <View style={styles.sessionTop}>
              <Text style={styles.sessionMeta}>{session.mode}</Text>
              <Text style={styles.sessionMeta}>Score {session.score}</Text>
            </View>
            <View style={styles.sessionTop}>
              <Text style={styles.sessionMetric}>Correct {session.correct_count}</Text>
              <Text style={styles.sessionMetric}>Streak {session.streak}</Text>
              <Text style={styles.sessionMetric}>{session.status}</Text>
            </View>
          </LearningCard>

          {answer && answeredQuestion ? (
            <LearningCard>
              <Text style={styles.prompt}>{answeredQuestion.prompt}</Text>
              <View style={styles.feedbackBox}>
                <CheckCircle2 size={20} color={answer.is_correct ? colors.success : colors.danger} />
                <Text style={styles.feedbackText}>
                  {answer.is_correct ? "Correct" : "Needs review"} · {answer.correct_answer}
                </Text>
              </View>
            </LearningCard>
          ) : question ? (
            <LearningCard>
              <View style={styles.timerPanel}>
                <View style={styles.timerMain}>
                  <Clock3 size={18} color={remainingSeconds <= 0 ? colors.danger : colors.primary} />
                  <Text style={[styles.timerText, remainingSeconds <= 0 && styles.timerTextDanger]}>
                    {timerStatus}
                  </Text>
                  <Text style={styles.timerMeta}>
                    / {timerTotalSeconds}s
                  </Text>
                </View>
                <Pressable
                  accessibilityRole="button"
                  disabled={!canExtendTimer}
                  onPress={extendTimer}
                  style={[styles.extendButton, !canExtendTimer && styles.extendButtonDisabled]}
                >
                  <TimerReset size={16} color={canExtendTimer ? colors.primary : colors.softText} />
                  <Text style={[styles.extendButtonText, !canExtendTimer && styles.extendButtonTextDisabled]}>
                    +{TIMER_EXTENSION_SECONDS}s
                  </Text>
                </Pressable>
              </View>
              <View style={styles.timerTrack}>
                <View
                  style={[
                    styles.timerFill,
                    {
                      width: `${Math.max(0, Math.min(100, timerPercent))}%`,
                      backgroundColor: remainingSeconds <= 5 ? colors.danger : colors.primary,
                    },
                  ]}
                />
              </View>
              <Text style={styles.prompt}>{question.prompt}</Text>
              <View style={question.option_layout === "compact" ? styles.compactOptions : undefined}>
                {question.options.map((option) => (
                  <Pressable
                    key={option}
                    accessibilityRole="button"
                    disabled={busy}
                    onPress={() => submit(option)}
                    style={question.option_layout === "compact" ? styles.compactChoice : styles.choice}
                  >
                    <Text style={question.option_layout === "compact" ? styles.compactChoiceText : styles.choiceText}>
                      {option}
                    </Text>
                    {question.option_layout === "compact" ? null : <Send size={16} color={colors.muted} />}
                  </Pressable>
                ))}
              </View>
            </LearningCard>
          ) : (
            <EmptyState title={session.is_finished ? "Session finished" : "No active question"} />
          )}

          {answer && session.current_question ? (
            <PrimaryButton
              label="Next question"
              Icon={PlayCircle}
              onPress={() => {
                setAnswer(null);
                setAnsweredQuestion(null);
              }}
            />
          ) : null}
          {!session.current_question && !session.is_finished ? (
            <PrimaryButton label="Finish session" Icon={Square} onPress={finish} disabled={busy} />
          ) : null}
          {session.is_finished ? (
            <SecondaryButton label="New quiz" Icon={PlayCircle} onPress={() => setSession(null)} />
          ) : (
            <View style={styles.actionGrid}>
              <SecondaryButton label="Save for later" Icon={Bookmark} onPress={saveCurrentQuizForLater} disabled={busy} />
              <SecondaryButton label="New setup" Icon={PlayCircle} onPress={resetCurrentQuiz} disabled={busy} />
            </View>
          )}
        </>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    marginBottom: spacing.md,
  },
  savedTop: {
    marginBottom: spacing.sm,
  },
  savedMeta: {
    color: colors.muted,
    fontWeight: "800",
    lineHeight: 20,
  },
  actionGrid: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  topicWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  topicChip: {
    minHeight: 42,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.72)",
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  countChip: {
    width: 58,
    minHeight: 42,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.72)",
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  topicChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  topicText: {
    color: colors.muted,
    fontWeight: "900",
  },
  topicTextActive: {
    color: "#FFFFFF",
  },
  spacer: {
    height: spacing.md,
  },
  sessionTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.sm,
  },
  sessionMeta: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  sessionMetric: {
    color: colors.muted,
    fontWeight: "800",
  },
  chip: {
    alignSelf: "flex-start",
    color: colors.primary,
    backgroundColor: colors.primarySoft,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    fontWeight: "900",
    marginBottom: spacing.md,
  },
  timerPanel: {
    minHeight: 52,
    borderRadius: radius.lg,
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginBottom: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  timerMain: {
    flexDirection: "row",
    alignItems: "center",
  },
  timerText: {
    color: colors.primary,
    fontSize: typography.heading,
    fontWeight: "900",
    marginLeft: spacing.sm,
  },
  timerTextDanger: {
    color: colors.danger,
  },
  timerMeta: {
    color: colors.muted,
    fontWeight: "800",
    marginLeft: spacing.xs,
  },
  extendButton: {
    minHeight: 34,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primary,
    paddingHorizontal: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  extendButtonDisabled: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  },
  extendButtonText: {
    color: colors.primary,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  extendButtonTextDisabled: {
    color: colors.softText,
  },
  timerTrack: {
    height: 9,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceMuted,
    overflow: "hidden",
    marginBottom: spacing.lg,
  },
  timerFill: {
    height: 9,
    borderRadius: radius.pill,
  },
  prompt: {
    color: colors.ink,
    fontSize: 23,
    fontWeight: "900",
    lineHeight: 32,
    marginBottom: spacing.md,
    textAlign: "center",
  },
  subtitle: {
    color: colors.muted,
    fontWeight: "700",
    marginBottom: spacing.lg,
  },
  instruction: {
    color: colors.muted,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  compactOptions: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.md,
  },
  compactChoice: {
    minHeight: 50,
    minWidth: "31%",
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  compactChoiceText: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    textAlign: "center",
  },
  choice: {
    minHeight: 58,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    marginTop: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  choiceText: {
    flex: 1,
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "800",
    marginRight: spacing.md,
  },
  feedbackBox: {
    borderRadius: radius.lg,
    backgroundColor: colors.sageSoft,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    marginTop: spacing.lg,
  },
  feedbackText: {
    flex: 1,
    color: colors.ink,
    fontWeight: "900",
    marginLeft: spacing.md,
  },
});
