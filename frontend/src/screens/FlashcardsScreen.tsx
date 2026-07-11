import React, {useCallback, useEffect, useRef, useState} from "react";
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

import {platformApi} from "../api/platform";
import {
  AnimatedEntrance,
  EmptyState,
  ErrorState,
  LearningCard,
  LoadingState,
  PrimaryButton,
  ProgressBar,
  ScreenContainer,
  ScreenHeader,
  SecondaryButton,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {
  FlashcardBoxSummary,
  FlashcardRating,
  FlashcardState,
  QuestionType,
  TargetCategory,
} from "../types/api";

const QUESTION_TYPES: Array<{key: QuestionType; label: string; Icon: LucideIcon}> = [
  {key: "brandGeneric", label: "نام تجاری", Icon: Sparkles},
  {key: "timing", label: "با غذا / بی غذا", Icon: Layers},
  {key: "indication", label: "اندیکاسیون", Icon: Sparkles},
  {key: "sideEffects", label: "عوارض", Icon: Layers},
  {key: "classification", label: "دسته‌بندی", Icon: Sparkles},
  {key: "dosageForm", label: "اشکال دارویی", Icon: Layers},
  {key: "dosing", label: "دوزینگ", Icon: Sparkles},
  {key: "pregnancy", label: "بارداری / شیردهی", Icon: Layers},
  {key: "doseAdjustment", label: "تنظیم دوز", Icon: Sparkles},
];

type FlowStep = "entry" | "category" | "cards";
type StudyMode = "new" | "leitner";

export function FlashcardsScreen() {
  const {token} = useAuth();
  const [step, setStep] = useState<FlowStep>("entry");
  const [mode, setMode] = useState<StudyMode>("new");
  const [selectedQuestionType, setSelectedQuestionType] = useState<QuestionType | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [categories, setCategories] = useState<TargetCategory[]>([]);
  const [cards, setCards] = useState<FlashcardState[]>([]);
  const [boxSummary, setBoxSummary] = useState<FlashcardBoxSummary | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reviewedCardIdsRef = useRef<number[]>([]);

  const loadEntrySummary = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setBoxSummary(await platformApi.flashcardBoxes(token));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Leitner summary unavailable.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadEntrySummary();
  }, [loadEntrySummary]);

  async function chooseQuestionType(questionType: QuestionType) {
    if (!token) return;
    setBusy(true);
    setError(null);
    setSelectedQuestionType(questionType);
    setSelectedCategory("");
    setMode("new");
    try {
      setCategories(await platformApi.targetCategories(token, questionType));
      setStep("category");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Categories unavailable.");
    } finally {
      setBusy(false);
    }
  }

  async function openNewDeck(categoryKey: string) {
    if (!token || !selectedQuestionType) return;
    setBusy(true);
    setLoading(true);
    setError(null);
    setSelectedCategory(categoryKey);
    setMode("new");
    reviewedCardIdsRef.current = [];
    try {
      await platformApi.seedFlashcards(token, categoryKey, selectedQuestionType);
      setCards(await platformApi.flashcards(token, "new", categoryKey, selectedQuestionType));
      setRevealed(false);
      setStep("cards");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not open new flashcards.");
    } finally {
      setBusy(false);
      setLoading(false);
    }
  }

  async function openLeitner() {
    if (!token) return;
    setBusy(true);
    setLoading(true);
    setError(null);
    setMode("leitner");
    setSelectedQuestionType(null);
    setSelectedCategory("");
    reviewedCardIdsRef.current = [];
    try {
      const [cardPayload, summaryPayload] = await Promise.all([
        platformApi.flashcards(token, "leitner"),
        platformApi.flashcardBoxes(token),
      ]);
      setCards(cardPayload);
      setBoxSummary(summaryPayload);
      setRevealed(false);
      setStep("cards");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not open Leitner box.");
    } finally {
      setBusy(false);
      setLoading(false);
    }
  }

  async function review(rating: FlashcardRating) {
    const currentCard = cards[0];
    if (!token || !currentCard) return;
    setBusy(true);
    setError(null);
    try {
      await platformApi.reviewFlashcard(token, currentCard.id, rating);
      reviewedCardIdsRef.current = [...reviewedCardIdsRef.current, currentCard.id];
      const remainingCards = cards.slice(1);
      if (remainingCards.length) {
        setCards(remainingCards);
      } else {
        setLoading(true);
        const nextCards = await platformApi.flashcards(
          token,
          mode,
          selectedCategory,
          selectedQuestionType ?? undefined,
          reviewedCardIdsRef.current,
        );
        setCards(nextCards);
        setLoading(false);
      }
      setRevealed(false);
      if (mode === "leitner") {
        setBoxSummary(await platformApi.flashcardBoxes(token));
      }
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Review failed.");
      setLoading(false);
    } finally {
      setBusy(false);
    }
  }

  function goBack() {
    setError(null);
    setRevealed(false);
    if (step === "cards" && mode === "new") {
      setCards([]);
      setStep("category");
      return;
    }
    setCards([]);
    setCategories([]);
    setSelectedQuestionType(null);
    setSelectedCategory("");
    reviewedCardIdsRef.current = [];
    setStep("entry");
  }

  const currentCard = cards[0];
  const totalCards = cards.length;
  const selectedQuestionLabel =
    QUESTION_TYPES.find((item) => item.key === selectedQuestionType)?.label ?? "";
  const selectedCategoryLabel =
    categories.find((category) => category.key === selectedCategory)?.label ?? "همه دسته‌ها";
  const headerEyebrow =
    step === "entry"
      ? "Step 1 · Choose a path"
      : step === "category"
        ? `Step 2 · ${selectedQuestionLabel}`
        : mode === "leitner"
          ? "Global Leitner review"
          : `${selectedQuestionLabel} · ${selectedCategoryLabel}`;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={headerEyebrow}
        title={step === "cards" ? (mode === "leitner" ? "Leitner Box" : "New Cards") : "Flashcards"}
        action={
          step === "entry" ? null : (
            <Pressable accessibilityRole="button" onPress={goBack} style={styles.backButton}>
              <ArrowLeft size={20} color={colors.ink} />
            </Pressable>
          )
        }
      />

      {error ? <ErrorState message={error} onRetry={step === "entry" ? loadEntrySummary : undefined} /> : null}

      {step === "entry" ? (
        <AnimatedEntrance>
          <Text style={styles.stepTitle}>چه چیزی را می‌خواهی مرور کنی؟</Text>
          <Text style={styles.stepDescription}>
            یک نوع سؤال برای کارت‌های جدید انتخاب کن، یا مستقیماً وارد جعبه سراسری لایتنر شو.
          </Text>

          <Pressable
            accessibilityRole="button"
            disabled={busy}
            onPress={openLeitner}
            style={({pressed}) => [styles.leitnerCard, pressed && styles.pressed]}
          >
            <View style={styles.leitnerIcon}>
              <FolderOpen size={28} color={colors.black} />
            </View>
            <View style={styles.optionCopy}>
              <Text style={styles.optionTitle}>باز کردن جعبه لایتنر</Text>
              <Text style={styles.optionMeta}>صف سراسری رفع اشکال، مستقل از نوع سؤال و دسته‌بندی</Text>
            </View>
            <View style={styles.countBadge}>
              <Text style={styles.countValue}>{loading ? "…" : boxSummary?.total ?? 0}</Text>
              <Text style={styles.countLabel}>cards</Text>
            </View>
          </Pressable>

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
                  <Text style={styles.optionMeta}>{category.count} knowledge sources</Text>
                </View>
              </Pressable>
            ))}
          </View>
        </AnimatedEntrance>
      ) : null}

      {step === "cards" ? (
        loading ? (
          <LoadingState label={mode === "leitner" ? "Opening Leitner box" : "Preparing new cards"} />
        ) : !currentCard ? (
          <AnimatedEntrance>
            <EmptyState title={mode === "leitner" ? "جعبه لایتنر خالی است" : "کارت جدیدی در این مسیر باقی نمانده"} />
            <PrimaryButton
              label={mode === "leitner" ? "بررسی دوباره جعبه" : "انتخاب مسیر دیگر"}
              Icon={mode === "leitner" ? RefreshCw : RotateCcw}
              onPress={mode === "leitner" ? openLeitner : goBack}
              disabled={busy}
            />
          </AnimatedEntrance>
        ) : (
          <AnimatedEntrance>
            <View style={styles.sessionTop}>
              <View>
                <Text style={styles.sessionTitle}>
                  {mode === "leitner" ? `Box ${currentCard.box}` : "New"}
                </Text>
                <Text style={styles.sessionMeta}>
                  {mode === "leitner"
                    ? `${currentCard.source_type} · ${currentCard.target_category_label || "All"}`
                    : `${selectedQuestionLabel} · ${selectedCategoryLabel}`}
                </Text>
              </View>
              <View style={styles.remainingBadge}>
                <Text style={styles.remainingValue}>{totalCards}</Text>
                <Text style={styles.remainingLabel}>remaining</Text>
              </View>
            </View>
            <ProgressBar value={Math.max(8, 100 / Math.max(1, totalCards))} />

            <Pressable
              key={`${currentCard.id}:${revealed ? "answer" : "prompt"}`}
              accessibilityRole="button"
              onPress={() => setRevealed((value) => !value)}
              style={[styles.flashcard, revealed && styles.flashcardRevealed]}
            >
              <View style={styles.cardTop}>
                <View style={styles.cardBadge}>
                  {revealed ? <Eye size={20} color={colors.primary} /> : <Layers size={20} color={colors.secondary} />}
                </View>
                <View>
                  <Text style={styles.cardState}>{revealed ? "ANSWER" : "QUESTION"}</Text>
                  <Text style={styles.cardStateMeta}>
                    {mode === "leitner" ? `Leitner box ${currentCard.box}` : "Outside Leitner"}
                  </Text>
                </View>
              </View>

              <View style={styles.cardBody}>
                <Text style={revealed ? styles.answer : styles.prompt}>
                  {revealed ? currentCard.correct_answer : currentCard.prompt}
                </Text>
                {revealed && currentCard.feedback ? (
                  <Text style={styles.feedback}>{currentCard.feedback}</Text>
                ) : null}
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
                ? "این کارت Due نیست؛ فقط پاسخ اشتباه آن را وارد جعبه اول می‌کند."
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
    minHeight: 112,
    borderRadius: radius.lg,
    backgroundColor: colors.primary,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: colors.primary,
    shadowOpacity: 0.22,
    shadowRadius: 18,
    shadowOffset: {width: 0, height: 8},
  },
  leitnerIcon: {
    width: 54,
    height: 54,
    borderRadius: radius.lg,
    backgroundColor: "rgba(0,16,20,0.12)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
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
    backgroundColor: colors.black,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: spacing.md,
  },
  countValue: {
    color: colors.primary,
    fontSize: 18,
    fontWeight: "900",
  },
  countLabel: {
    color: colors.muted,
    fontSize: 9,
    fontWeight: "800",
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
    fontWeight: "900",
    textAlign: "right",
  },
  optionCardMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    textAlign: "right",
    marginTop: spacing.xs,
  },
  pressed: {
    transform: [{scale: 0.98}],
    opacity: 0.9,
  },
  categoryList: {
    gap: spacing.md,
  },
  categoryCard: {
    minHeight: 78,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    flexDirection: "row",
    alignItems: "center",
  },
  categoryIcon: {
    width: 46,
    height: 46,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceMuted,
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
    color: colors.primary,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  sessionMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  remainingBadge: {
    minWidth: 70,
    minHeight: 50,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  remainingValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  remainingLabel: {
    color: colors.muted,
    fontSize: 9,
    fontWeight: "800",
  },
  flashcard: {
    minHeight: 480,
    borderRadius: radius.xl,
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    padding: spacing.xl,
    justifyContent: "space-between",
    marginTop: spacing.lg,
    shadowColor: "#000000",
    shadowOpacity: 0.34,
    shadowRadius: 26,
    shadowOffset: {width: 0, height: 12},
  },
  flashcardRevealed: {
    backgroundColor: "#0D3A3B",
  },
  cardTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  cardBadge: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  cardState: {
    color: colors.ink,
    fontSize: typography.small,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  cardStateMeta: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    marginTop: 2,
  },
  cardBody: {
    flex: 1,
    justifyContent: "center",
  },
  prompt: {
    color: colors.ink,
    fontSize: 27,
    fontWeight: "900",
    lineHeight: 38,
    textAlign: "center",
  },
  answer: {
    color: colors.primary,
    fontSize: 27,
    fontWeight: "900",
    lineHeight: 38,
    textAlign: "center",
  },
  feedback: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 22,
    textAlign: "center",
    marginTop: spacing.lg,
  },
  reviewActions: {
    gap: spacing.sm,
  },
  ruleHint: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 20,
    textAlign: "center",
    marginTop: spacing.md,
  },
});
