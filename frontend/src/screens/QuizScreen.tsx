import AsyncStorage from "@react-native-async-storage/async-storage";
import Slider from "@react-native-community/slider";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import React, {useEffect, useMemo, useRef, useState} from "react";
import {Animated, Pressable, StyleSheet, Text, View} from "react-native";
import {Bookmark, CheckCircle2, Clock3, Flame, PlayCircle, RefreshCw, Sparkles, Square, TimerReset, Trash2, XCircle} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {
  CelebrationParticles,
  EmptyState,
  ErrorState,
  LearningCard,
  LoadingState,
  PrimaryButton,
  ProgressBar,
  ProgressRing,
  ScreenContainer,
  SecondaryButton,
  SkeletonCard,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import {AVAILABLE_QUIZ_TYPES, useQuizStore} from "../store/quiz";
import type {GameAnswer, GameQuestion, GameSession, TargetCategory, Topic} from "../types/api";

const SAVED_QUIZ_SESSION_KEY = "pharmexa_saved_quiz_session";
const DEFAULT_QUESTION_SECONDS = 30;
const TIMER_EXTENSION_SECONDS = 30;

type SavedQuizSession = {
  id: number;
  userId: number | null;
  questionType: string;
  mode: "random" | "category";
  count: number;
  targetCategoryKey: string;
  score: number;
  correctCount: number;
  savedAt: string;
};

type QuizStep = "type" | "mode" | "count" | "category" | "play" | "result";

function formatMode(mode: "random" | "category") {
  return mode === "category" ? "دسته‌بندی‌شده" : "تصادفی";
}

function StreakFire({streak}: {streak: number}) {
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    scale.stopAnimation();
    scale.setValue(1);
    if (!streak) return;

    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(scale, {toValue: 1.18, duration: 520, useNativeDriver: true}),
        Animated.timing(scale, {toValue: 1, duration: 520, useNativeDriver: true}),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [scale, streak]);

  if (!streak) return null;

  return (
    <View style={styles.streakBadge}>
      <Animated.View style={{transform: [{scale}]}}>
        <Flame size={17} color={colors.amber} fill={colors.amber} />
      </Animated.View>
      <Text style={styles.streakText}>{streak} streak</Text>
    </View>
  );
}

export function QuizScreen() {
  const {token, user} = useAuth();
  const queryClient = useQueryClient();
  const {
    selectedQuestionTypeKey,
    selectedQuestionTypeId,
    selectedTopicId,
    selectedMode,
    selectedCategoryKey,
    selectedCount,
    setQuestionType,
    syncTopicFromTopics,
    setMode,
    setCategoryKey,
    setCount,
    resetSetup,
  } = useQuizStore();

  const [step, setStep] = useState<QuizStep>("type");
  const [session, setSession] = useState<GameSession | null>(null);
  const [savedSession, setSavedSession] = useState<SavedQuizSession | null>(null);
  const [answer, setAnswer] = useState<GameAnswer | null>(null);
  const [answeredQuestion, setAnsweredQuestion] = useState<GameQuestion | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(DEFAULT_QUESTION_SECONDS);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showReminderCallout, setShowReminderCallout] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [levelUp, setLevelUp] = useState(false);

  const topicsQuery = useQuery({
    queryKey: ["quiz-topics", token],
    queryFn: () => platformApi.topics(token!),
    enabled: Boolean(token),
  });

  const categoriesQuery = useQuery({
    queryKey: ["target-categories", token, selectedQuestionTypeKey],
    queryFn: () => platformApi.targetCategories(token!, selectedQuestionTypeKey),
    enabled: Boolean(token) && Boolean(selectedQuestionTypeKey),
  });

  useEffect(() => {
    if (!topicsQuery.data?.length) return;
    syncTopicFromTopics(topicsQuery.data);
  }, [syncTopicFromTopics, topicsQuery.data]);

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

  useEffect(() => {
    if (!levelUp) return;
    const timeout = setTimeout(() => setLevelUp(false), 1300);
    return () => clearTimeout(timeout);
  }, [levelUp]);

  const categories = categoriesQuery.data ?? [];
  const availableTopics = useMemo(
    () => (topicsQuery.data ?? []).filter((topic) => AVAILABLE_QUIZ_TYPES.some((item) => item.key === topic.key)),
    [topicsQuery.data],
  );
  const questionTypeLabel =
    AVAILABLE_QUIZ_TYPES.find((item) => item.key === selectedQuestionTypeKey)?.label ?? "";
  const selectedCategory = categories.find((item) => item.key === selectedCategoryKey);
  const activeQuestion = session?.current_question ?? null;
  const displayQuestion = answer && answeredQuestion ? answeredQuestion : activeQuestion;
  const timerTotalSeconds = activeQuestion?.timer_total_seconds ?? session?.timer_seconds ?? DEFAULT_QUESTION_SECONDS;
  const timerPercent = timerTotalSeconds ? (remainingSeconds / timerTotalSeconds) * 100 : 0;
  const canExtendTimer = Boolean(activeQuestion?.timer_extension_available && !answer);
  const choiceState = useMemo(() => {
    if (!answer || !displayQuestion) return new Map<string, "neutral" | "correct" | "wrong">();
    const map = new Map<string, "neutral" | "correct" | "wrong">();
    displayQuestion.options.forEach((option) => {
      if (option === answer.correct_answer) {
        map.set(option, "correct");
      } else if (option === selectedOption && !answer.is_correct) {
        map.set(option, "wrong");
      } else {
        map.set(option, "neutral");
      }
    });
    return map;
  }, [answer, displayQuestion, selectedOption]);

  const startMutation = useMutation({
    mutationFn: () =>
      platformApi.startGame(
        token!,
        selectedTopicId!,
        selectedMode,
        selectedCount,
        selectedMode === "category" ? selectedCategoryKey : "",
      ),
    onSuccess: (nextSession) => {
      setSession(nextSession);
      setStep("play");
      setAnswer(null);
      setAnsweredQuestion(null);
      setSelectedOption(null);
      setShowReminderCallout(false);
    },
  });

  const answerMutation = useMutation({
    mutationFn: (selected_answer: string) =>
      platformApi.answerQuestion(token!, session!.id, activeQuestion!.id, selected_answer),
    onSuccess: (result, selected_answer) => {
      const previousLevel = Math.floor((session?.score ?? 0) / 100);
      const nextLevel = Math.floor((result.game.score ?? 0) / 100);
      setSelectedOption(selected_answer);
      setAnswer(result.answer);
      setAnsweredQuestion(activeQuestion);
      setSession(result.game);
      setLevelUp(nextLevel > previousLevel);
      setShowReminderCallout(true);
      setFeedbackMessage(
        result.answer.is_correct
          ? "آفرین! پاسخ درست بود."
          : "این سؤال را برای مرور ذخیره کن.",
      );
    },
  });

  const finishMutation = useMutation({
    mutationFn: () => platformApi.finishGame(token!, session!.id),
    onSuccess: async (nextSession) => {
      setSession(nextSession);
      setStep("result");
      setAnswer(null);
      setSelectedOption(null);
      setShowReminderCallout(false);
      await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
      setSavedSession(null);
      queryClient.invalidateQueries({queryKey: ["dashboard"]});
      queryClient.invalidateQueries({queryKey: ["statistics"]});
      queryClient.invalidateQueries({queryKey: ["quiz-history"]});
    },
  });

  const extendMutation = useMutation({
    mutationFn: () => platformApi.extendGameTimer(token!, session!.id),
    onSuccess: (nextSession) => setSession(nextSession),
  });

  const pauseMutation = useMutation({
    mutationFn: () => platformApi.pauseGame(token!, session!.id),
    onSuccess: async (paused) => {
      const payload: SavedQuizSession = {
        id: paused.id,
        userId: user?.id ?? null,
        questionType: paused.topic_key,
        mode: paused.mode === "category" ? "category" : "random",
        count: paused.total_questions,
        targetCategoryKey: paused.target_category_key,
        score: paused.score,
        correctCount: paused.correct_count,
        savedAt: new Date().toISOString(),
      };
      await AsyncStorage.setItem(SAVED_QUIZ_SESSION_KEY, JSON.stringify(payload));
      setSavedSession(payload);
      setSession(null);
      setStep("type");
    },
  });

  const resumeMutation = useMutation({
    mutationFn: () => platformApi.resumeGame(token!, savedSession!.id),
    onSuccess: async (nextSession) => {
      setSession(nextSession);
      const nextTopic = topicsQuery.data?.find((item) => item.key === nextSession.topic_key);
      if (nextTopic) setQuestionType(nextTopic);
      setMode(nextSession.mode === "category" ? "category" : "random");
      setCount(nextSession.total_questions);
      setCategoryKey(nextSession.target_category_key);
      setStep("play");
      await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
      setSavedSession(null);
    },
  });

  const reminderMutation = useMutation({
    mutationFn: () =>
      platformApi.createQuizReminder(token!, {
        game_session_id: session?.id,
        game_question_id: answeredQuestion?.id,
        knowledge_source_id: undefined,
        question_type: answeredQuestion?.question_type ?? selectedQuestionTypeId,
        prompt: answeredQuestion?.prompt ?? "",
        selected_answer: selectedOption ?? "",
        correct_answer: answer?.correct_answer ?? "",
        explanation: feedbackMessage,
        options: answeredQuestion?.options ?? [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ["quiz-reminders"]});
      setShowReminderCallout(false);
      setFeedbackMessage("سؤال برای مرور بعدی ذخیره شد.");
    },
  });

  function resetQuizFlow() {
    resetSetup();
    setSession(null);
    setSavedSession(null);
    setAnswer(null);
    setAnsweredQuestion(null);
    setSelectedOption(null);
    setShowReminderCallout(false);
    setFeedbackMessage("");
    setLevelUp(false);
    setStep("type");
  }

  function openNextQuestion() {
    setAnswer(null);
    setAnsweredQuestion(null);
    setSelectedOption(null);
    setShowReminderCallout(false);
    setFeedbackMessage("");
    setLevelUp(false);
    if (!session?.current_question) {
      setStep("result");
    }
  }

  async function discardSavedQuiz() {
    await AsyncStorage.removeItem(SAVED_QUIZ_SESSION_KEY);
    setSavedSession(null);
  }

  if (categoriesQuery.isLoading && selectedMode === "category" && step === "category") {
    return (
      <ScreenContainer>
        <SkeletonCard height={72} />
        <SkeletonCard height={260} />
      </ScreenContainer>
    );
  }

  if (topicsQuery.isLoading || startMutation.isPending || resumeMutation.isPending) {
    return (
      <ScreenContainer>
        <SkeletonCard height={72} />
        <SkeletonCard height={220} />
        <SkeletonCard height={96} />
      </ScreenContainer>
    );
  }

  if (topicsQuery.error) {
    return (
      <ErrorState
        message={topicsQuery.error instanceof Error ? topicsQuery.error.message : "بارگذاری نوع سؤال ممکن نیست."}
        onRetry={() => topicsQuery.refetch()}
      />
    );
  }

  const resultAccuracy = session?.total_questions
    ? Math.round(((session.correct_count ?? 0) / Math.max(1, session.total_questions)) * 100)
    : 0;

  return (
    <ScreenContainer>
      <View style={styles.quizTitleWrap}>
        <Text style={styles.quizTitle}>آزمون مرحله‌ای</Text>
        {session ? <Text style={styles.quizSubtitle}>{questionTypeLabel} · {formatMode(selectedMode)}</Text> : null}
      </View>

      {startMutation.error ? (
        <ErrorState
          message={startMutation.error instanceof Error ? startMutation.error.message : "شروع آزمون با خطا مواجه شد."}
          onRetry={() => startMutation.mutate()}
        />
      ) : null}
      {answerMutation.error ? (
        <ErrorState
          message={answerMutation.error instanceof Error ? answerMutation.error.message : "ثبت پاسخ با خطا مواجه شد."}
        />
      ) : null}

      {savedSession && !session ? (
        <LearningCard tone="amber">
          <Text style={styles.label}>آزمون ذخیره‌شده</Text>
          <Text style={styles.helperText}>
            {savedSession.score} امتیاز · {savedSession.correctCount} پاسخ صحیح
          </Text>
          <View style={styles.actionRow}>
            <PrimaryButton label="ادامه آزمون" Icon={RefreshCw} onPress={() => resumeMutation.mutate()} />
            <SecondaryButton label="حذف" Icon={Trash2} onPress={discardSavedQuiz} />
          </View>
        </LearningCard>
      ) : null}

      {step === "type" ? (
        <LearningCard>
          <Text style={styles.selectionTitle}>نوع سؤال</Text>
          <View style={styles.selectionGrid}>
            {availableTopics.map((item: Topic) => {
              const active = selectedTopicId === item.id;
              return (
                <Pressable
                  key={item.id}
                  accessibilityRole="button"
                  onPress={() => {
                    setQuestionType(item);
                    setStep("mode");
                  }}
                  style={[styles.selectionBox, active && styles.selectionBoxActive]}
                >
                  {active ? (
                    <View style={styles.selectionCheck}>
                      <CheckCircle2 size={16} color="#FFFFFF" />
                    </View>
                  ) : null}
                  <Text style={[styles.selectionText, active && styles.selectionTextActive]}>{item.label}</Text>
                  {item.detail ? <Text style={[styles.selectionMeta, active && styles.selectionMetaActive]}>{item.detail}</Text> : null}
                </Pressable>
              );
            })}
          </View>
        </LearningCard>
      ) : null}

      {step === "mode" ? (
        <LearningCard tone="mint">
          <Text style={styles.selectionTitle}>شیوه آزمون</Text>
          <View style={styles.selectionGrid}>
            {([
              {key: "random", label: "تصادفی", meta: "سؤال‌ها از همه منابع فعال همین نوع انتخاب می‌شوند."},
              {key: "category", label: "دسته‌بندی‌شده", meta: "بعد از تعداد، دسته‌بندی دارویی را انتخاب می‌کنی."},
            ] as const).map((item) => {
              const active = selectedMode === item.key;
              return (
                <Pressable
                  key={item.key}
                  accessibilityRole="button"
                  onPress={() => {
                    setMode(item.key);
                    setStep("count");
                  }}
                  style={[styles.selectionBox, active && styles.selectionBoxActive]}
                >
                  {active ? (
                    <View style={styles.selectionCheck}>
                      <CheckCircle2 size={16} color="#FFFFFF" />
                    </View>
                  ) : null}
                  <Text style={[styles.selectionText, active && styles.selectionTextActive]}>{item.label}</Text>
                  <Text style={[styles.selectionMeta, active && styles.selectionMetaActive]}>{item.meta}</Text>
                </Pressable>
              );
            })}
          </View>
          <View style={styles.actionRow}>
            <SecondaryButton label="مرحله قبل" onPress={() => setStep("type")} />
          </View>
        </LearningCard>
      ) : null}

      {step === "count" ? (
        <LearningCard tone="blue">
          <Text style={styles.label}>تعداد سؤال</Text>
          <Text style={styles.sliderValue}>{selectedCount} سؤال</Text>
          <Slider
            minimumValue={5}
            maximumValue={50}
            step={5}
            inverted
            minimumTrackTintColor={colors.primary}
            maximumTrackTintColor={colors.borderStrong}
            thumbTintColor={colors.primary}
            value={selectedCount}
            onValueChange={(value) => setCount(Math.round(value / 5) * 5)}
          />
          <View style={styles.sliderLabels}>
            <Text style={styles.sliderLabel}>50</Text>
            <Text style={styles.sliderLabel}>5</Text>
          </View>
          <View style={styles.actionRow}>
            <SecondaryButton label="مرحله قبل" onPress={() => setStep("mode")} />
            <PrimaryButton
              label={selectedMode === "category" ? "مرحله بعد" : "شروع آزمون"}
              onPress={() => {
                if (selectedMode === "category") {
                  setStep("category");
                  return;
                }
                startMutation.mutate();
              }}
              disabled={!selectedTopicId}
            />
          </View>
        </LearningCard>
      ) : null}

      {step === "category" ? (
        <LearningCard tone="sage">
          <Text style={styles.selectionTitle}>انتخاب دسته‌بندی</Text>
          {categoriesQuery.error ? (
            <ErrorState
              message={categoriesQuery.error instanceof Error ? categoriesQuery.error.message : "بارگذاری دسته‌بندی‌ها ممکن نیست."}
              onRetry={() => categoriesQuery.refetch()}
            />
          ) : categories.length ? (
            <View style={styles.selectionGrid}>
              {categories.map((category: TargetCategory) => {
                const active = selectedCategoryKey === category.key;
                return (
                  <Pressable
                    key={category.key}
                    accessibilityRole="button"
                    onPress={() => setCategoryKey(category.key)}
                    style={[styles.selectionBox, active && styles.selectionBoxActive]}
                  >
                    {active ? (
                      <View style={styles.selectionCheck}>
                        <CheckCircle2 size={16} color="#FFFFFF" />
                      </View>
                    ) : null}
                    <Text style={[styles.selectionText, active && styles.selectionTextActive]}>{category.label}</Text>
                    <Text style={[styles.selectionMeta, active && styles.selectionMetaActive]}>{category.count} سؤال آماده</Text>
                  </Pressable>
                );
              })}
            </View>
          ) : (
            <EmptyState title="دسته‌ای برای این نوع سؤال پیدا نشد" />
          )}
          <View style={styles.actionRow}>
            <SecondaryButton label="مرحله قبل" onPress={() => setStep("count")} />
            <PrimaryButton
              label="شروع آزمون"
              onPress={() => startMutation.mutate()}
              disabled={!selectedCategoryKey || !selectedTopicId}
            />
          </View>
        </LearningCard>
      ) : null}

      {step === "play" && session ? (
        <>
          <LearningCard tone="primary">
            <View style={styles.playHeader}>
              <View>
                <Text style={styles.sessionMeta}>{questionTypeLabel}</Text>
                <Text style={styles.helperText}>
                  {formatMode(selectedMode)} · {session.correct_count} صحیح · {session.score} امتیاز
                </Text>
                <StreakFire streak={session.streak} />
              </View>
              <ProgressRing value={timerPercent} size={86} strokeWidth={8} label={`${remainingSeconds}`} />
            </View>
            <View style={styles.playHeaderMeta}>
              <Text style={styles.timerText}>
                <Clock3 size={16} color={remainingSeconds <= 5 ? colors.danger : colors.primary} />{" "}
                {remainingSeconds <= 0 ? "زمان تمام شد" : `${remainingSeconds} ثانیه باقی مانده`}
              </Text>
              <SecondaryButton
                label={`+${TIMER_EXTENSION_SECONDS} ثانیه`}
                Icon={TimerReset}
                onPress={() => extendMutation.mutate()}
                disabled={!canExtendTimer || extendMutation.isPending}
              />
            </View>
          </LearningCard>

          {displayQuestion ? (
            <LearningCard style={styles.questionCard}>
              <CelebrationParticles active={Boolean(answer?.is_correct)} />
              {displayQuestion.instruction ? <Text style={styles.instruction}>{displayQuestion.instruction}</Text> : null}
              <Text style={styles.prompt}>{displayQuestion.prompt}</Text>
              <View style={styles.choicesWrap}>
                {displayQuestion.options.map((option) => {
                  const state = choiceState.get(option) ?? "neutral";
                  const selected = selectedOption === option;
                  return (
                    <Pressable
                      key={option}
                      accessibilityRole="button"
                      disabled={Boolean(answer) || answerMutation.isPending}
                      onPress={() => answerMutation.mutate(option)}
                      style={[
                        styles.choice,
                        state === "correct" && styles.choiceCorrect,
                        state === "wrong" && styles.choiceWrong,
                        selected && !answer && styles.choiceSelected,
                      ]}
                    >
                      <Text
                        style={[
                          styles.choiceText,
                          (state === "correct" || state === "wrong" || (selected && !answer)) && styles.choiceTextActive,
                        ]}
                      >
                        {option}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              {answer ? (
                <View style={[styles.feedbackPanel, levelUp && styles.feedbackLevelUp]}>
                  {levelUp ? (
                    <View style={styles.levelUpRow}>
                      <Sparkles size={15} color={colors.primary} />
                      <Text style={styles.levelUpText}>سطح آزمون بالا رفت!</Text>
                    </View>
                  ) : null}
                  <View style={styles.feedbackTop}>
                    {answer.is_correct ? (
                      <CheckCircle2 size={20} color={colors.success} />
                    ) : (
                      <XCircle size={20} color={colors.danger} />
                    )}
                    <Text style={styles.feedbackTitle}>{feedbackMessage}</Text>
                  </View>
                  <Text style={styles.feedbackText}>پاسخ صحیح: {answer.correct_answer}</Text>
                  {answeredQuestion?.explanation ? (
                    <Text style={styles.feedbackDescription}>{answeredQuestion.explanation}</Text>
                  ) : null}
                  {showReminderCallout ? (
                    <Pressable
                      accessibilityRole="button"
                      onPress={() => reminderMutation.mutate()}
                      style={styles.reminderBox}
                    >
                      <Bookmark size={18} color={colors.primary} />
                      <Text style={styles.reminderText}>یادآوری</Text>
                    </Pressable>
                  ) : null}
                </View>
              ) : null}
            </LearningCard>
          ) : (
            <EmptyState title="سؤال فعالی باقی نمانده است" />
          )}

          <View style={styles.actionColumn}>
            {answer && session.current_question ? (
              <PrimaryButton label="سؤال بعدی" Icon={PlayCircle} onPress={openNextQuestion} />
            ) : null}
            {!session.current_question ? (
              <PrimaryButton
                label="اتمام آزمون"
                Icon={Square}
                onPress={() => finishMutation.mutate()}
                disabled={finishMutation.isPending}
              />
            ) : null}
            <SecondaryButton
              label="ذخیره برای بعد"
              Icon={Bookmark}
              onPress={() => pauseMutation.mutate()}
              disabled={pauseMutation.isPending}
            />
            <SecondaryButton label="بازنشانی تنظیمات" Icon={RefreshCw} onPress={resetQuizFlow} />
          </View>
        </>
      ) : null}

      {step === "result" && session ? (
        <LearningCard tone="mint" style={styles.resultCard}>
          <CelebrationParticles active />
          <Text style={styles.wizardTitle}>اتمام آزمون</Text>
          <Text style={styles.resultValue}>{resultAccuracy}%</Text>
          <Text style={styles.helperText}>
            {session.correct_count} پاسخ صحیح از {session.total_questions} سؤال
          </Text>
          <Text style={styles.helperText}>امتیاز نهایی: {session.score}</Text>
          <View style={styles.resultStreak}>
            <StreakFire streak={session.streak} />
          </View>
          <View style={styles.actionRow}>
            <PrimaryButton label="آزمون جدید" Icon={PlayCircle} onPress={resetQuizFlow} />
          </View>
        </LearningCard>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  quizTitleWrap: {
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.lg,
  },
  quizTitle: {
    color: colors.ink,
    fontSize: 28,
    fontWeight: "900",
    textAlign: "center",
  },
  quizSubtitle: {
    color: colors.muted,
    fontWeight: "800",
    marginTop: spacing.xs,
    textAlign: "center",
  },
  wizardTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginBottom: spacing.sm,
    textAlign: "center",
  },
  label: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    marginBottom: spacing.md,
  },
  helperText: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 22,
    marginTop: spacing.xs,
    marginBottom: spacing.sm,
  },
  selectionTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    textAlign: "center",
    marginBottom: spacing.lg,
  },
  selectionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  selectionBox: {
    width: "48%",
    minHeight: 124,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: spacing.md,
    position: "relative",
  },
  selectionBoxActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    shadowColor: colors.primary,
    shadowOpacity: 0.3,
    shadowRadius: 16,
    shadowOffset: {width: 0, height: 8},
    elevation: 4,
  },
  selectionCheck: {
    position: "absolute",
    top: spacing.sm,
    right: spacing.sm,
    width: 24,
    height: 24,
    borderRadius: radius.pill,
    backgroundColor: "rgba(15,23,42,0.22)",
    alignItems: "center",
    justifyContent: "center",
  },
  selectionText: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    textAlign: "center",
  },
  selectionTextActive: {
    color: colors.black,
  },
  selectionMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 19,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  selectionMetaActive: {
    color: "rgba(0,16,20,0.72)",
  },
  optionChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  optionText: {
    color: colors.muted,
    fontWeight: "900",
  },
  optionTextActive: {
    color: colors.black,
  },
  sliderValue: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: "900",
    textAlign: "center",
    marginBottom: spacing.sm,
  },
  sliderLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  sliderLabel: {
    color: colors.muted,
    fontWeight: "700",
  },
  actionRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  actionColumn: {
    gap: spacing.sm,
  },
  playHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  playHeaderMeta: {
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  sessionMeta: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  streakBadge: {
    alignSelf: "flex-start",
    minHeight: 30,
    borderRadius: radius.pill,
    backgroundColor: colors.amberSoft,
    borderWidth: 1,
    borderColor: "rgba(244,198,106,0.38)",
    paddingHorizontal: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    marginTop: spacing.sm,
  },
  streakText: {
    color: colors.amber,
    fontSize: 11,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  timerText: {
    color: colors.ink,
    fontWeight: "800",
  },
  questionCard: {
    backgroundColor: colors.surfaceElevated,
    overflow: "hidden",
  },
  instruction: {
    color: colors.secondary,
    fontWeight: "900",
    marginBottom: spacing.sm,
    textAlign: "center",
  },
  prompt: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
    lineHeight: 31,
    textAlign: "center",
    marginBottom: spacing.md,
  },
  choicesWrap: {
    gap: spacing.sm,
  },
  choice: {
    minHeight: 54,
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  choiceSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySoft,
  },
  choiceCorrect: {
    borderColor: colors.success,
    backgroundColor: colors.primarySoft,
  },
  choiceWrong: {
    borderColor: colors.danger,
    backgroundColor: colors.roseSoft,
  },
  choiceText: {
    color: colors.ink,
    fontWeight: "800",
    textAlign: "center",
  },
  choiceTextActive: {
    color: colors.black,
    fontWeight: "900",
  },
  feedbackPanel: {
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  feedbackLevelUp: {
    borderColor: colors.primary,
    shadowColor: colors.primary,
    shadowOpacity: 0.38,
    shadowRadius: 18,
    shadowOffset: {width: 0, height: 0},
    elevation: 6,
  },
  levelUpRow: {
    alignSelf: "flex-start",
    minHeight: 28,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.sm,
    marginBottom: spacing.sm,
  },
  levelUpText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  feedbackTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  feedbackTitle: {
    color: colors.ink,
    fontWeight: "900",
    marginLeft: spacing.sm,
  },
  feedbackText: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.sm,
  },
  feedbackDescription: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 22,
    marginTop: spacing.sm,
  },
  reminderBox: {
    marginTop: spacing.md,
    alignSelf: "flex-start",
    minHeight: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primary,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.md,
  },
  reminderText: {
    color: colors.primary,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  resultCard: {
    overflow: "hidden",
  },
  resultStreak: {
    alignItems: "center",
    marginTop: spacing.sm,
  },
  resultValue: {
    color: colors.primary,
    fontSize: 42,
    fontWeight: "900",
    textAlign: "center",
    marginVertical: spacing.md,
  },
});
