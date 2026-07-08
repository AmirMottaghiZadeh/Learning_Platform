import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {useCallback, useEffect, useRef, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {Bookmark, CheckCircle2, ChevronLeft, ChevronRight, Eye, Layers, Plus, RotateCcw, Trash2, XCircle} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {EmptyState, ErrorState, LearningCard, LoadingState, PrimaryButton, ScreenContainer, ScreenHeader, SecondaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {FlashcardBoxSummary, FlashcardDeckSummary, FlashcardRating, FlashcardState, QuestionType, TargetCategory} from "../types/api";

const QUESTION_TYPES: Array<{key: QuestionType; label: string}> = [
  {key: "brandGeneric", label: "نام تجاری"},
  {key: "timing", label: "با غذا / بی غذا"},
  {key: "indication", label: "اندیکاسیون"},
  {key: "sideEffects", label: "عوارض"},
];

const SAVED_FLASHCARD_DECK_KEY = "k_game_saved_flashcard_deck";

type SavedFlashcardDeck = {
  userId: number | null;
  questionType: QuestionType;
  categoryKey: string;
  box: number | null;
  savedAt: string;
};

export function FlashcardsScreen() {
  const {token, user} = useAuth();
  const [cards, setCards] = useState<FlashcardState[]>([]);
  const [boxSummary, setBoxSummary] = useState<FlashcardBoxSummary | null>(null);
  const [deckSummary, setDeckSummary] = useState<FlashcardDeckSummary | null>(null);
  const [categories, setCategories] = useState<TargetCategory[]>([]);
  const [selectedQuestionType, setSelectedQuestionType] = useState<QuestionType>("brandGeneric");
  const [selectedBox, setSelectedBox] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [savedDeck, setSavedDeck] = useState<SavedFlashcardDeck | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [cardIndex, setCardIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadRequestRef = useRef(0);
  const avoidNextCardIdRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    const requestId = loadRequestRef.current + 1;
    loadRequestRef.current = requestId;
    setLoading(true);
    setError(null);
    try {
      const [cardPayload, boxPayload, deckPayload, categoryPayload] = await Promise.all([
        platformApi.flashcards(token, selectedBox ?? undefined, selectedCategory, selectedQuestionType),
        platformApi.flashcardBoxes(token, selectedCategory, selectedQuestionType),
        platformApi.flashcardDeckSummary(token, selectedCategory, selectedQuestionType),
        platformApi.targetCategories(token, selectedQuestionType),
      ]);
      if (requestId !== loadRequestRef.current) return;
      const avoidedCardId = avoidNextCardIdRef.current;
      let nextCards = cardPayload;
      if (avoidedCardId && cardPayload.length > 1 && cardPayload[0]?.id === avoidedCardId) {
        const nextCardIndex = cardPayload.findIndex((item) => item.id !== avoidedCardId);
        if (nextCardIndex > 0) {
          nextCards = [
            cardPayload[nextCardIndex],
            ...cardPayload.slice(0, nextCardIndex),
            ...cardPayload.slice(nextCardIndex + 1),
          ];
        }
      }
      avoidNextCardIdRef.current = null;
      setCards(nextCards);
      setCardIndex(0);
      setBoxSummary(boxPayload);
      setDeckSummary(deckPayload);
      setCategories(categoryPayload);
      if (selectedCategory && !categoryPayload.some((category) => category.key === selectedCategory)) {
        setCards([]);
        setCardIndex(0);
        setSelectedCategory("");
        setSelectedBox(null);
      }
      setRevealed(false);
    } catch (exc) {
      if (requestId !== loadRequestRef.current) return;
      setCards([]);
      setCardIndex(0);
      setBoxSummary(null);
      setDeckSummary(null);
      setError(exc instanceof Error ? exc.message : "Flashcards unavailable.");
    } finally {
      if (requestId === loadRequestRef.current) setLoading(false);
    }
  }, [selectedBox, selectedCategory, selectedQuestionType, token]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    let active = true;
    async function loadSavedDeck() {
      try {
        const raw = await AsyncStorage.getItem(SAVED_FLASHCARD_DECK_KEY);
        if (!raw) {
          if (active) setSavedDeck(null);
          return;
        }
        const parsed = JSON.parse(raw) as SavedFlashcardDeck;
        if (parsed.userId && user?.id && parsed.userId !== user.id) {
          if (active) setSavedDeck(null);
          return;
        }
        if (active) setSavedDeck(parsed);
      } catch {
        await AsyncStorage.removeItem(SAVED_FLASHCARD_DECK_KEY);
        if (active) setSavedDeck(null);
      }
    }
    loadSavedDeck();
    return () => {
      active = false;
    };
  }, [user?.id]);

  async function review(rating: FlashcardRating) {
    const currentCard = cards[cardIndex] ?? cards[0];
    if (!token || !currentCard) return;
    const currentCardId = currentCard.id;
    setBusy(true);
    setLoading(true);
    avoidNextCardIdRef.current = currentCardId;
    setCards([]);
    setCardIndex(0);
    setRevealed(false);
    try {
      await platformApi.reviewFlashcard(token, currentCardId, rating);
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Review failed.");
    } finally {
      setBusy(false);
    }
  }

  async function seedCards() {
    if (!token) return;
    setBusy(true);
    setLoading(true);
    setCards([]);
    setCardIndex(0);
    setError(null);
    try {
      await platformApi.seedFlashcards(token, selectedCategory, selectedQuestionType);
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not create review cards.");
    } finally {
      setBusy(false);
    }
  }

  function resetVisibleCards() {
    loadRequestRef.current += 1;
    avoidNextCardIdRef.current = (cards[cardIndex] ?? cards[0])?.id ?? null;
    setCards([]);
    setCardIndex(0);
    setBoxSummary(null);
    setDeckSummary(null);
    setRevealed(false);
    setError(null);
    setLoading(true);
  }

  function chooseCategory(categoryKey: string) {
    if (categoryKey === selectedCategory) return;
    resetVisibleCards();
    setSelectedCategory(categoryKey);
    setSelectedBox(null);
  }

  function chooseQuestionType(questionType: QuestionType) {
    if (questionType === selectedQuestionType) return;
    resetVisibleCards();
    setSelectedQuestionType(questionType);
    setSelectedCategory("");
    setSelectedBox(null);
  }

  function chooseBox(box: number | null) {
    if (box === selectedBox) return;
    resetVisibleCards();
    setSelectedBox(box);
  }

  async function saveCurrentDeckForLater() {
    const payload: SavedFlashcardDeck = {
      userId: user?.id ?? null,
      questionType: selectedQuestionType,
      categoryKey: selectedCategory,
      box: selectedBox,
      savedAt: new Date().toISOString(),
    };
    await AsyncStorage.setItem(SAVED_FLASHCARD_DECK_KEY, JSON.stringify(payload));
    setSavedDeck(payload);
  }

  async function resumeSavedDeck() {
    if (!savedDeck) return;
    const isCurrentSelection =
      savedDeck.questionType === selectedQuestionType &&
      savedDeck.categoryKey === selectedCategory &&
      savedDeck.box === selectedBox;
    resetVisibleCards();
    setSelectedQuestionType(savedDeck.questionType);
    setSelectedCategory(savedDeck.categoryKey);
    setSelectedBox(savedDeck.box);
    await AsyncStorage.removeItem(SAVED_FLASHCARD_DECK_KEY);
    setSavedDeck(null);
    if (isCurrentSelection) {
      await load();
    }
  }

  async function discardSavedDeck() {
    await AsyncStorage.removeItem(SAVED_FLASHCARD_DECK_KEY);
    setSavedDeck(null);
  }

  function goToPreviousCard() {
    if (cards.length <= 1) return;
    setRevealed(false);
    setCardIndex((index) => (index - 1 + cards.length) % cards.length);
  }

  function goToNextCard() {
    if (cards.length <= 1) return;
    setRevealed(false);
    setCardIndex((index) => (index + 1) % cards.length);
  }

  const card = cards[cardIndex] ?? cards[0];
  const selectedCategoryLabel = categories.find((category) => category.key === selectedCategory)?.label ?? "All";
  const selectedQuestionLabel = QUESTION_TYPES.find((type) => type.key === selectedQuestionType)?.label ?? "";
  const dueCount = deckSummary?.due_cards ?? boxSummary?.new ?? cards.length;
  const savedDeckQuestionLabel = savedDeck
    ? QUESTION_TYPES.find((type) => type.key === savedDeck.questionType)?.label ?? savedDeck.questionType
    : "";
  const savedDeckCategoryLabel = savedDeck?.categoryKey
    ? categories.find((category) => category.key === savedDeck.categoryKey)?.label ?? savedDeck.categoryKey
    : "All";

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={selectedBox ? `Leitner review · ${selectedQuestionLabel} · ${selectedCategoryLabel} · Box ${selectedBox}` : `Leitner review · ${selectedQuestionLabel} · ${selectedCategoryLabel}`}
        title="Flashcards"
      />
      {savedDeck ? (
        <LearningCard tone="amber">
          <Text style={styles.sectionLabel}>روند ذخیره‌شده</Text>
          <Text style={styles.savedMeta}>
            {savedDeckQuestionLabel} · {savedDeckCategoryLabel} · {savedDeck.box ? `Box ${savedDeck.box}` : "Due"}
          </Text>
          <View style={styles.actionGrid}>
            <PrimaryButton label="ادامه" Icon={RotateCcw} onPress={resumeSavedDeck} disabled={busy} />
            <SecondaryButton label="حذف" Icon={Trash2} onPress={discardSavedDeck} disabled={busy} />
          </View>
        </LearningCard>
      ) : null}
      <LearningCard tone="lavender">
        <Text style={styles.sectionLabel}>نوع سؤال</Text>
        <View style={styles.boxRow}>
          {QUESTION_TYPES.map((type) => (
            <Pressable
              key={type.key}
              accessibilityRole="button"
              onPress={() => chooseQuestionType(type.key)}
              style={[styles.categoryChip, selectedQuestionType === type.key && styles.boxChipActive]}
            >
              <Text style={[styles.boxText, selectedQuestionType === type.key && styles.boxTextActive]}>
                {type.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </LearningCard>
      <LearningCard tone="mint">
        <Text style={styles.sectionLabel}>Category</Text>
        <View style={styles.boxRow}>
          <Pressable
            accessibilityRole="button"
            onPress={() => chooseCategory("")}
            style={[styles.categoryChip, !selectedCategory && styles.boxChipActive]}
          >
            <Text style={[styles.boxText, !selectedCategory && styles.boxTextActive]}>All</Text>
          </Pressable>
          {categories.map((category) => (
            <Pressable
              key={category.key}
              accessibilityRole="button"
              onPress={() => chooseCategory(category.key)}
              style={[styles.categoryChip, selectedCategory === category.key && styles.boxChipActive]}
            >
              <Text style={[styles.boxText, selectedCategory === category.key && styles.boxTextActive]}>
                {category.label} · {category.count}
              </Text>
            </Pressable>
          ))}
        </View>
      </LearningCard>
      <LearningCard tone="blue">
        <Text style={styles.sectionLabel}>Leitner boxes</Text>
        {deckSummary ? (
          <View style={styles.deckStats}>
            <View style={styles.deckStat}>
              <Text style={styles.deckStatValue}>{deckSummary.eligible_sources}</Text>
              <Text style={styles.deckStatLabel}>Sources</Text>
            </View>
            <View style={styles.deckStat}>
              <Text style={styles.deckStatValue}>{deckSummary.scheduled_cards}</Text>
              <Text style={styles.deckStatLabel}>Cards</Text>
            </View>
            <View style={styles.deckStat}>
              <Text style={styles.deckStatValue}>{deckSummary.unscheduled_sources}</Text>
              <Text style={styles.deckStatLabel}>New</Text>
            </View>
          </View>
        ) : null}
        <View style={styles.boxRow}>
          <Pressable
            accessibilityRole="button"
            onPress={() => chooseBox(null)}
            style={[styles.boxChip, selectedBox === null && styles.boxChipActive]}
          >
            <Text style={[styles.boxText, selectedBox === null && styles.boxTextActive]}>
              Due · {dueCount}
            </Text>
          </Pressable>
          {boxSummary?.boxes.map((item) => (
            <Pressable
              key={item.box}
              accessibilityRole="button"
              onPress={() => chooseBox(item.box)}
              style={[styles.boxChip, selectedBox === item.box && styles.boxChipActive]}
            >
              <Text style={[styles.boxText, selectedBox === item.box && styles.boxTextActive]}>
                {item.box} · {item.count}
              </Text>
            </Pressable>
          ))}
        </View>
        <View style={styles.actionGrid}>
          <SecondaryButton label="ذخیره روند فعلی" Icon={Bookmark} onPress={saveCurrentDeckForLater} disabled={busy} />
        </View>
      </LearningCard>
      {loading ? (
        <LoadingState label="Loading flashcards" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : !card ? (
        <>
          <EmptyState title={selectedBox ? "This box is empty" : "No cards in this deck"} />
          <PrimaryButton
            label={deckSummary?.unscheduled_sources ? "Create all cards" : "Refresh deck"}
            Icon={Plus}
            onPress={seedCards}
            disabled={busy}
          />
        </>
      ) : (
        <>
          <View style={styles.flashcardShell}>
            <Pressable
              accessibilityLabel="کارت قبلی"
              accessibilityRole="button"
              disabled={cards.length <= 1 || busy}
              onPress={goToPreviousCard}
              style={[styles.cardNavButton, styles.cardNavButtonLeft, (cards.length <= 1 || busy) && styles.cardNavButtonDisabled]}
            >
              <ChevronLeft size={22} color={colors.muted} />
            </Pressable>
            <Pressable
              key={`${selectedQuestionType}:${selectedCategory}:${selectedBox ?? "due"}:${card.id}:${revealed ? "back" : "front"}`}
              accessibilityRole="button"
              onPress={() => setRevealed((value) => !value)}
              style={[styles.flashcard, revealed ? styles.flashcardBack : styles.flashcardFront]}
            >
              <View style={styles.cardTop}>
                <View style={styles.badge}>
                  <Layers size={20} color={revealed ? colors.rose : colors.sage} />
                </View>
                <View>
                  <Text style={styles.state}>{revealed ? "پشت کارت" : "روی کارت"}</Text>
                  <Text style={styles.stateMeta}>
                    {card.box ? `Box ${card.box}` : "New"} · {cardIndex + 1}/{cards.length}
                  </Text>
                </View>
              </View>
              {revealed ? (
                <>
                  <View style={styles.cardBody}>
                    <Text style={styles.answer}>{card.correct_answer}</Text>
                    {card.feedback ? <Text style={styles.feedback}>{card.feedback}</Text> : null}
                  </View>
                  <View style={styles.cardStageActions}>
                    <View style={styles.feedbackBar}>
                      <Pressable
                        accessibilityRole="button"
                        disabled={busy}
                        onPress={() => review("hard")}
                        style={({pressed}) => [styles.feedbackChip, pressed && !busy && styles.feedbackChipPressed]}
                      >
                        <Text style={styles.feedbackChipText}>Hard</Text>
                      </Pressable>
                      <Pressable
                        accessibilityRole="button"
                        disabled={busy}
                        onPress={() => review("good")}
                        style={({pressed}) => [styles.feedbackChip, pressed && !busy && styles.feedbackChipPressed]}
                      >
                        <Text style={styles.feedbackChipText}>Good</Text>
                      </Pressable>
                      <Pressable
                        accessibilityRole="button"
                        disabled={busy}
                        onPress={() => review("easy")}
                        style={({pressed}) => [styles.feedbackChip, pressed && !busy && styles.feedbackChipPressed]}
                      >
                        <Text style={styles.feedbackChipText}>Easy</Text>
                      </Pressable>
                    </View>
                    <View style={styles.reviewGrid}>
                      <SecondaryButton label="بلد نبودم" Icon={XCircle} onPress={() => review("unknown")} disabled={busy} />
                      <PrimaryButton label="بلد بودم" Icon={CheckCircle2} onPress={() => review("known")} disabled={busy} />
                    </View>
                    <SecondaryButton
                      label="نمایش سؤال"
                      Icon={RotateCcw}
                      onPress={() => setRevealed(false)}
                      disabled={busy}
                    />
                  </View>
                </>
              ) : (
                <>
                  <View style={styles.cardBody}>
                    <Text style={styles.prompt}>{card.prompt}</Text>
                  </View>
                  <View style={styles.cardStageActions}>
                    <SecondaryButton
                      label="نمایش پاسخ"
                      Icon={Eye}
                      onPress={() => setRevealed(true)}
                      disabled={busy}
                    />
                  </View>
                </>
              )}
            </Pressable>
            <Pressable
              accessibilityLabel="کارت بعدی"
              accessibilityRole="button"
              disabled={cards.length <= 1 || busy}
              onPress={goToNextCard}
              style={[styles.cardNavButton, styles.cardNavButtonRight, (cards.length <= 1 || busy) && styles.cardNavButtonDisabled]}
            >
              <ChevronRight size={22} color={colors.muted} />
            </Pressable>
          </View>

        </>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    marginBottom: spacing.md,
  },
  savedMeta: {
    color: colors.muted,
    fontWeight: "800",
    lineHeight: 20,
    marginBottom: spacing.sm,
  },
  actionGrid: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  boxRow: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  deckStats: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  deckStat: {
    flex: 1,
    minHeight: 64,
    borderRadius: radius.lg,
    backgroundColor: "rgba(255,255,255,0.72)",
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  deckStatValue: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  deckStatLabel: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "800",
  },
  boxChip: {
    minHeight: 40,
    minWidth: 78,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.74)",
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  categoryChip: {
    minHeight: 40,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.74)",
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  boxChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  boxText: {
    color: colors.muted,
    fontWeight: "900",
  },
  boxTextActive: {
    color: "#FFFFFF",
  },
  flashcardShell: {
    minHeight: 430,
    marginBottom: spacing.md,
    position: "relative",
  },
  flashcard: {
    minHeight: 430,
    borderRadius: radius.lg,
    borderWidth: 1,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.xl,
    justifyContent: "space-between",
    shadowColor: "#24172A",
    shadowOpacity: 0.08,
    shadowRadius: 20,
    shadowOffset: {width: 0, height: 10},
    elevation: 2,
  },
  flashcardFront: {
    backgroundColor: colors.surface,
    borderColor: colors.primaryMuted,
  },
  flashcardBack: {
    backgroundColor: colors.mintSoft,
    borderColor: "#BBDACF",
  },
  cardNavButton: {
    position: "absolute",
    top: "45%",
    zIndex: 5,
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#24172A",
    shadowOpacity: 0.08,
    shadowRadius: 10,
    shadowOffset: {width: 0, height: 4},
    elevation: 2,
  },
  cardNavButtonLeft: {
    left: spacing.xs,
  },
  cardNavButtonRight: {
    right: spacing.xs,
  },
  cardNavButtonDisabled: {
    opacity: 0.35,
  },
  cardTop: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  badge: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surfaceMuted,
    marginRight: spacing.md,
  },
  state: {
    color: colors.muted,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  stateMeta: {
    color: colors.softText,
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  prompt: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: "900",
    lineHeight: 34,
    textAlign: "center",
    marginVertical: spacing.xl,
  },
  cardBody: {
    flex: 1,
    justifyContent: "center",
  },
  cardStageActions: {
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  answer: {
    color: colors.ink,
    fontSize: 25,
    lineHeight: 35,
    fontWeight: "900",
    textAlign: "center",
    marginVertical: spacing.lg,
  },
  feedback: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 20,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  feedbackBar: {
    minHeight: 38,
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
  },
  feedbackChip: {
    minWidth: 74,
    minHeight: 32,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  feedbackChipPressed: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  feedbackChipText: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "900",
  },
  reviewGrid: {
    gap: spacing.sm,
  },
});
