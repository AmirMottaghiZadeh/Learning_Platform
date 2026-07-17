import React from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {
  ArrowLeft,
  CheckCircle2,
  Eye,
  FolderOpen,
  Layers,
  RefreshCw,
  RotateCcw,
  Sparkles,
  XCircle,
} from "lucide-react-native";
import type {LucideIcon} from "lucide-react-native";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";

import {platformApi} from "../api/platform";
import {
  AnimatedEntrance,
  EmptyState,
  ErrorState,
  LearningCard,
  PrimaryButton,
  ProgressBar,
  ScreenContainer,
  ScreenHeader,
  SecondaryButton,
  SkeletonCard,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import {useFlashcardsStore} from "../store/flashcards";
import type {FlashcardRating, QuestionType} from "../types/api";

const QUESTION_TYPES: Array<{key: QuestionType; label: string; Icon: LucideIcon}> = [
  {key: "brandGeneric", label: "نام تجاری", Icon: Sparkles},
  {key: "timing", label: "با غذا / بی غذا", Icon: Layers},
];
const FLASHCARD_BATCH_SIZE = 20;
const FLASHCARD_PREFETCH_THRESHOLD = 5;

export function FlashcardsScreen() {
  const {token} = useAuth();
  const queryClient = useQueryClient();
  const [leitnerPickerOpen, setLeitnerPickerOpen] = React.useState(false);
  const [batchRequest, setBatchRequest] = React.useState(0);
  const [hasMoreCards, setHasMoreCards] = React.useState(true);
  const nextBatchAfterId = React.useRef(0);
  const {
    step,
    mode,
    selectedQuestionType,
    selectedCategory,
    selectedLeitnerBox,
    categories,
    cards,
    revealed,
    setStep,
    setMode,
    setSelectedQuestionType,
    setSelectedCategory,
    setSelectedLeitnerBox,
    setCategories,
    setCards,
    appendCards,
    removeCard,
    prependCard,
    setRevealed,
    resetFlow,
  } = useFlashcardsStore();

  const entrySummaryQuery = useQuery({
    queryKey: ["flashcard-boxes", token],
    queryFn: () => platformApi.flashcardBoxes(token!),
    enabled: Boolean(token),
  });

  const categoriesQuery = useQuery({
    queryKey: ["flashcard-categories", token, selectedQuestionType],
    queryFn: () => platformApi.targetCategories(token!, selectedQuestionType ?? undefined),
    enabled: Boolean(token) && step === "category" && Boolean(selectedQuestionType),
  });

  const cardsQuery = useQuery({
    queryKey: [
      "flashcard-batch",
      token,
      mode,
      selectedCategory,
      selectedQuestionType,
      selectedLeitnerBox,
      batchRequest,
    ],
    queryFn: () =>
      platformApi.flashcards(
        token!,
        mode,
        selectedCategory,
        selectedQuestionType ?? undefined,
        [],
        selectedLeitnerBox,
        FLASHCARD_BATCH_SIZE,
        nextBatchAfterId.current,
      ),
    enabled: Boolean(token) && step === "cards" && hasMoreCards,
  });

  React.useEffect(() => {
    if (categoriesQuery.data) setCategories(categoriesQuery.data);
  }, [categoriesQuery.data, setCategories]);

  React.useEffect(() => {
    if (!cardsQuery.data) return;
    appendCards(cardsQuery.data);
    const lastCardId = cardsQuery.data[cardsQuery.data.length - 1]?.id;
    if (lastCardId) {
      nextBatchAfterId.current = lastCardId;
    }
    if (cardsQuery.data.length < FLASHCARD_BATCH_SIZE) {
      setHasMoreCards(false);
    }
  }, [appendCards, cardsQuery.data]);

  React.useEffect(() => {
    if (
      step !== "cards" ||
      !hasMoreCards ||
      cards.length === 0 ||
      cards.length > FLASHCARD_PREFETCH_THRESHOLD ||
      cardsQuery.isFetching
    ) {
      return;
    }
    setBatchRequest((value) => value + 1);
  }, [batchRequest, cards.length, cardsQuery.isFetching, hasMoreCards, step]);

  function resetCardQueue() {
    setCards([]);
    nextBatchAfterId.current = 0;
    setHasMoreCards(true);
    setBatchRequest((value) => value + 1);
  }

  const openNewDeckMutation = useMutation({
    mutationFn: async (categoryKey: string) => {
      await platformApi.seedFlashcards(token!, categoryKey, selectedQuestionType!);
      return categoryKey;
    },
    onSuccess: async (categoryKey) => {
      setSelectedCategory(categoryKey);
      setMode("new");
      setRevealed(false);
      resetCardQueue();
      setStep("cards");
      await Promise.all([
        queryClient.invalidateQueries({queryKey: ["flashcard-boxes", token]}),
      ]);
    },
  });

  const reviewMutation = useMutation({
    mutationFn: ({cardId, rating}: {card: (typeof cards)[number]; cardId: number; rating: FlashcardRating}) =>
      platformApi.reviewFlashcard(token!, cardId, rating),
    onMutate: ({card, cardId}) => {
      removeCard(cardId);
      setRevealed(false);
      return {card};
    },
    onError: (_error, variables, context) => {
      if (context?.card) {
        prependCard(context.card);
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["flashcard-boxes", token],
        refetchType: "none",
      });
      void queryClient.invalidateQueries({queryKey: ["statistics"], refetchType: "none"});
      void queryClient.invalidateQueries({queryKey: ["dashboard"], refetchType: "none"});
    },
  });

  function chooseQuestionType(questionType: QuestionType) {
    setLeitnerPickerOpen(false);
    setSelectedQuestionType(questionType);
    setSelectedCategory("");
    setSelectedLeitnerBox(null);
    setMode("new");
    setRevealed(false);
    setStep("category");
  }

  function openNewDeck(categoryKey: string) {
    if (!selectedQuestionType) return;
    openNewDeckMutation.mutate(categoryKey);
  }

  function openLeitner(box?: number) {
    setLeitnerPickerOpen(false);
    setMode("leitner");
    setSelectedQuestionType(null);
    setSelectedCategory("");
    setSelectedLeitnerBox(box ?? null);
    resetCardQueue();
    setRevealed(false);
    setStep("cards");
  }

  function review(rating: FlashcardRating) {
    const currentCard = cards[0];
    if (!currentCard) return;
    reviewMutation.mutate({card: currentCard, cardId: currentCard.id, rating});
  }

  function goBack() {
    setRevealed(false);
    if (step === "cards") {
      void entrySummaryQuery.refetch();
    }
    if (step === "cards" && mode === "new") {
      setCards([]);
      setHasMoreCards(true);
      setStep("category");
      return;
    }
    resetFlow();
  }

  const currentCard = cards[0];
  const totalCards = cards.length;
  const selectedQuestionLabel =
    QUESTION_TYPES.find((item) => item.key === selectedQuestionType)?.label ?? "";
  const selectedCategoryLabel =
    categories.find((category) => category.key === selectedCategory)?.label ?? "همه دسته‌ها";
  const selectedLeitnerBoxSummary =
    entrySummaryQuery.data?.boxes.find((item) => item.box === selectedLeitnerBox) ?? null;
  const leitnerBoxes =
    entrySummaryQuery.data?.boxes ?? Array.from({length: 5}, (_, index) => ({box: index + 1, count: 0}));
  const headerEyebrow =
    step === "entry"
      ? "مرحله ۱ · انتخاب مسیر"
      : step === "category"
        ? `مرحله ۲ · ${selectedQuestionLabel}`
        : mode === "leitner"
          ? selectedLeitnerBox
            ? `مرور جعبه ${selectedLeitnerBox} لایتنر`
            : "مرور جعبه لایتنر"
          : `${selectedQuestionLabel} · ${selectedCategoryLabel}`;
  const loading = step === "cards" ? cards.length === 0 && cardsQuery.isFetching : entrySummaryQuery.isLoading;
  const busy = openNewDeckMutation.isPending || reviewMutation.isPending;
  const error =
    (entrySummaryQuery.error instanceof Error && entrySummaryQuery.error.message) ||
    (categoriesQuery.error instanceof Error && categoriesQuery.error.message) ||
    (cardsQuery.error instanceof Error && cardsQuery.error.message) ||
    (openNewDeckMutation.error instanceof Error && openNewDeckMutation.error.message) ||
    (reviewMutation.error instanceof Error && reviewMutation.error.message) ||
    null;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={headerEyebrow}
        title={step === "cards" ? (mode === "leitner" ? "جعبه لایتنر" : "فلش‌کارت‌های جدید") : "فلش‌کارت"}
        action={
          step === "entry" ? null : (
            <Pressable accessibilityRole="button" onPress={goBack} style={styles.backButton}>
              <ArrowLeft size={20} color={colors.ink} />
            </Pressable>
          )
        }
      />

      {error ? (
        <ErrorState
          message={error}
          onRetry={step === "entry" ? () => entrySummaryQuery.refetch() : undefined}
        />
      ) : null}

      {step === "entry" ? (
        <AnimatedEntrance>
          <Text style={styles.stepTitle}>چه چیزی را می‌خواهی مرور کنی؟</Text>
          <Text style={styles.stepDescription}>
            یک نوع سؤال برای کارت‌های جدید انتخاب کن، یا مستقیماً وارد جعبه سراسری لایتنر شو.
          </Text>

          <View style={[styles.leitnerCard, leitnerPickerOpen && styles.leitnerCardExpanded]}>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{expanded: leitnerPickerOpen, disabled: busy}}
              disabled={busy}
              onPress={() => setLeitnerPickerOpen((isOpen) => !isOpen)}
              style={({pressed}) => [styles.leitnerCardHeader, pressed && styles.pressed]}
            >
              <View style={styles.leitnerIcon}>
                <FolderOpen size={28} color={colors.primary} />
              </View>
              <View style={styles.optionCopy}>
                <Text style={styles.leitnerTitle}>جعبه لایتنر</Text>
                <Text style={styles.leitnerMeta}>برای مرور، یکی از جعبه‌های ۱ تا ۵ را انتخاب کن</Text>
              </View>
              <View style={styles.countBadge}>
                <Text style={styles.countValue}>{entrySummaryQuery.isLoading ? "…" : entrySummaryQuery.data?.total ?? 0}</Text>
                <Text style={styles.countLabel}>کارت</Text>
              </View>
            </Pressable>

            {leitnerPickerOpen ? (
              <View style={styles.leitnerBoxGrid}>
                {leitnerBoxes.map((item) => (
                <Pressable
                  key={item.box}
                  accessibilityRole="button"
                  disabled={busy || entrySummaryQuery.isLoading}
                  onPress={() => openLeitner(item.box)}
                  style={({pressed}) => [styles.leitnerBoxOption, pressed && styles.pressed]}
                >
                  <Text style={styles.leitnerBoxNumber}>جعبه {item.box}</Text>
                  <Text style={styles.leitnerBoxCount}>{entrySummaryQuery.isLoading ? "…" : item.count}</Text>
                  <Text style={styles.leitnerBoxLabel}>کارت</Text>
                </Pressable>
                ))}
              </View>
            ) : null}
          </View>

          <Text style={styles.orLabel}>یا یک نوع سؤال انتخاب کن</Text>
          <View style={styles.optionGrid}>
            {QUESTION_TYPES.map(({key, label, Icon}) => (
              <Pressable
                key={key}
                accessibilityRole="button"
                disabled={busy}
                onPress={() => chooseQuestionType(key)}
                style={({pressed}) => [styles.optionCard, pressed && styles.pressed]}
              >
                <View style={styles.optionIcon}>
                  <Icon size={21} color={colors.primary} />
                </View>
                <Text style={styles.optionCardTitle}>{label}</Text>
                <Text style={styles.optionCardMeta}>کارت‌های جدید</Text>
              </Pressable>
            ))}
          </View>
        </AnimatedEntrance>
      ) : null}

      {step === "category" ? (
        <AnimatedEntrance>
          <Text style={styles.stepTitle}>دسته‌بندی را انتخاب کن</Text>
          <Text style={styles.stepDescription}>
            بعد از انتخاب، کارت‌های جدید این مسیر مستقیماً نمایش داده می‌شوند.
          </Text>
          <View style={styles.categoryList}>
            <Pressable
              accessibilityRole="button"
              disabled={busy}
              onPress={() => openNewDeck("")}
              style={({pressed}) => [styles.categoryCard, pressed && styles.pressed]}
            >
              <View style={styles.categoryIcon}>
                <Layers size={20} color={colors.primary} />
              </View>
              <View style={styles.optionCopy}>
                <Text style={styles.optionTitle}>همه دسته‌ها</Text>
                <Text style={styles.optionMeta}>تمام کارت‌های جدید {selectedQuestionLabel}</Text>
              </View>
            </Pressable>
            {categories.map((category) => (
              <Pressable
                key={category.key}
                accessibilityRole="button"
                disabled={busy}
                onPress={() => openNewDeck(category.key)}
                style={({pressed}) => [styles.categoryCard, pressed && styles.pressed]}
              >
                <View style={styles.categoryIcon}>
                  <Sparkles size={20} color={colors.secondary} />
                </View>
                <View style={styles.optionCopy}>
                  <Text style={styles.optionTitle}>{category.label}</Text>
                  <Text style={styles.optionMeta}>{category.count} منبع سوال</Text>
                </View>
              </Pressable>
            ))}
          </View>
        </AnimatedEntrance>
      ) : null}

      {step === "cards" ? (
        loading ? (
          <>
            <SkeletonCard height={92} />
            <SkeletonCard height={360} />
            <SkeletonCard height={72} />
          </>
        ) : !currentCard ? (
          <AnimatedEntrance>
            <EmptyState title={mode === "leitner" ? "جعبه لایتنر خالی است" : "کارت جدیدی در این مسیر باقی نمانده"} />
            <PrimaryButton
              label={mode === "leitner" ? "بررسی دوباره جعبه" : "انتخاب مسیر دیگر"}
              Icon={mode === "leitner" ? RefreshCw : RotateCcw}
              onPress={mode === "leitner" ? () => openLeitner(selectedLeitnerBox ?? undefined) : goBack}
              disabled={busy}
            />
          </AnimatedEntrance>
        ) : (
          <AnimatedEntrance>
            <View style={styles.sessionTop}>
              <View>
                <Text style={styles.sessionTitle}>
                  {mode === "leitner" ? `جعبه ${currentCard.box}` : "جدید"}
                </Text>
                <Text style={styles.sessionMeta}>
                  {mode === "leitner"
                    ? `${selectedLeitnerBoxSummary ? `${selectedLeitnerBoxSummary.count} کارت در این جعبه · ` : ""}${QUESTION_TYPES.find((item) => item.key === currentCard.source_type)?.label ?? currentCard.source_type} · ${currentCard.target_category_label || "همه"}`
                    : `${selectedQuestionLabel} · ${selectedCategoryLabel}`}
                </Text>
              </View>
              <View style={styles.remainingBadge}>
                <Text style={styles.remainingValue}>{totalCards}</Text>
                <Text style={styles.remainingLabel}>در صف</Text>
              </View>
            </View>
            <ProgressBar value={Math.max(8, 100 / Math.max(1, totalCards))} />

            <Pressable
              key={`${currentCard.id}:${revealed ? "answer" : "prompt"}`}
              accessibilityRole="button"
              onPress={() => setRevealed(!revealed)}
              style={[styles.flashcard, revealed && styles.flashcardRevealed]}
            >
              <View style={styles.cardTop}>
                <View style={styles.cardBadge}>
                  {revealed ? <Eye size={20} color={colors.primary} /> : <Layers size={20} color={colors.secondary} />}
                </View>
                <View>
                  <Text style={styles.cardState}>{revealed ? "پاسخ" : "سؤال"}</Text>
                  <Text style={styles.cardStateMeta}>
                    {mode === "leitner" ? `جعبه ${currentCard.box}` : "کارت جدید"}
                  </Text>
                </View>
              </View>

              <View style={styles.cardBody}>
                <Text style={revealed ? styles.answer : styles.prompt}>
                  {revealed ? currentCard.correct_answer : currentCard.prompt}
                </Text>
              </View>

              {!revealed ? (
                <SecondaryButton label="نمایش پاسخ" Icon={Eye} onPress={() => setRevealed(true)} disabled={busy} />
              ) : (
                <View style={styles.reviewActions}>
                  <SecondaryButton
                    label={mode === "new" ? "اشتباه بود · ورود به Box 1" : "بلد نبودم"}
                    Icon={XCircle}
                    onPress={() => review("unknown")}
                    disabled={busy}
                  />
                  <PrimaryButton
                    label={mode === "new" ? "بلد بودم · تکمیل" : currentCard.box === 1 ? "بلد بودم · خروج از جعبه" : "بلد بودم"}
                    Icon={CheckCircle2}
                    onPress={() => review("known")}
                    disabled={busy}
                  />
                </View>
              )}
            </Pressable>

            <Text style={styles.ruleHint}>
              {mode === "new"
                ? "این کارت آماده مرور زمان‌دار نیست؛ فقط پاسخ اشتباه آن را وارد جعبه اول می‌کند."
                : "جعبه سراسری است و به نوع سؤال یا دسته‌بندی وابسته نیست."}
            </Text>
          </AnimatedEntrance>
        )
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  backButton: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  stepTitle: {
    color: colors.ink,
    fontSize: 23,
    fontWeight: "900",
    textAlign: "right",
  },
  stepDescription: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "700",
    lineHeight: 24,
    textAlign: "right",
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  leitnerCard: {
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    shadowColor: colors.primary,
    shadowOpacity: 0.22,
    shadowRadius: 18,
    shadowOffset: {width: 0, height: 8},
    overflow: "hidden",
  },
  leitnerCardExpanded: {
    borderColor: colors.primary,
  },
  leitnerCardHeader: {
    minHeight: 112,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
  },
  leitnerIcon: {
    width: 54,
    height: 54,
    borderRadius: radius.lg,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  leitnerTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  leitnerMeta: {
    color: colors.ink,
    opacity: 0.78,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  optionCopy: {
    flex: 1,
  },
  optionTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  optionMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  countBadge: {
    minWidth: 54,
    height: 54,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: spacing.md,
  },
  countValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  countLabel: {
    color: colors.muted,
    fontSize: 9,
    fontWeight: "800",
  },
  leitnerBoxGrid: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    justifyContent: "space-between",
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xs,
  },
  leitnerBoxOption: {
    width: "31%",
    minHeight: 98,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    padding: spacing.md,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  leitnerBoxNumber: {
    color: colors.ink,
    fontSize: typography.small,
    fontWeight: "900",
  },
  leitnerBoxCount: {
    color: colors.primary,
    fontSize: 23,
    fontWeight: "900",
    marginTop: spacing.xs,
  },
  leitnerBoxLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: 2,
  },
  orLabel: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "900",
    textAlign: "center",
    marginVertical: spacing.lg,
  },
  optionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  optionCard: {
    width: "48%",
    minHeight: 128,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
    justifyContent: "center",
  },
  optionIcon: {
    width: 42,
    height: 42,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  optionCardTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  optionCardMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  categoryList: {
    gap: spacing.md,
  },
  categoryCard: {
    minHeight: 86,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    flexDirection: "row",
    alignItems: "center",
  },
  categoryIcon: {
    width: 42,
    height: 42,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  sessionTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  sessionTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  sessionMeta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  remainingBadge: {
    minWidth: 72,
    minHeight: 72,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  remainingValue: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  remainingLabel: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
  },
  flashcard: {
    minHeight: 360,
    borderRadius: radius.xl,
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    padding: spacing.lg,
    marginTop: spacing.lg,
    justifyContent: "space-between",
  },
  flashcardRevealed: {
    borderColor: colors.primary,
  },
  cardTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  cardBadge: {
    width: 52,
    height: 52,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  cardState: {
    color: colors.ink,
    fontWeight: "900",
    fontSize: typography.body,
  },
  cardStateMeta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  cardBody: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  prompt: {
    color: colors.ink,
    fontSize: 24,
    fontWeight: "900",
    lineHeight: 34,
    textAlign: "center",
  },
  answer: {
    color: colors.primary,
    fontSize: 26,
    fontWeight: "900",
    lineHeight: 36,
    textAlign: "center",
    alignSelf: "center",
    width: "100%",
  },
  reviewActions: {
    gap: spacing.sm,
  },
  ruleHint: {
    color: colors.muted,
    fontWeight: "700",
    textAlign: "center",
    lineHeight: 22,
    marginTop: spacing.md,
  },
  pressed: {
    transform: [{scale: 0.99}],
  },
});
