import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { flashcardsApi } from "@/api/endpoints";
import { DeckCard, DeckCategory, DeckProgress } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { CardBackField, SectionChip } from "@/components/flashcards/CardParts";
import { LeitnerBox } from "@/components/flashcards/LeitnerBox";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { ICONS, IconImage, IconName } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

// --- topic decks: category grid -> topic list -> one topic's cards, in order

type Mode =
  | { kind: "categories" }
  | { kind: "topics"; category: string }
  | { kind: "deck"; topic: string; category: string }
  | { kind: "leitner" };

function iconFor(name: string, fallback: IconName): IconName {
  return name in ICONS ? (name as IconName) : fallback;
}

function ProgressBar({ value, height = 5 }: { value: number; height?: number }) {
  const { colors } = useTheme();
  const pct = Math.max(0, Math.min(1, value));
  return (
    <View style={{ height, borderRadius: height / 2, backgroundColor: colors.trackBg, overflow: "hidden" }}>
      <View style={{ width: `${pct * 100}%`, height, backgroundColor: colors.accent }} />
    </View>
  );
}

function LockedCard() {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <Card>
      <View style={{ alignItems: "center", gap: 12, paddingVertical: 24 }}>
        <View
          style={{
            width: 60,
            height: 60,
            borderRadius: 18,
            backgroundColor: colors.softBg,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <IconImage name="edu-flashcards" size={34} />
        </View>
        <AppText weight="800" size={15}>
          {t("comingSoon")}
        </AppText>
        <AppText muted weight="600" size={13} center>
          {t("lockedFeature")}
        </AppText>
      </View>
    </Card>
  );
}

/** The card itself: the drug and which section it asks about on the front,
 * that section's facts on the back. */
function FlipCard({ card, flipped, onFlip }: { card: DeckCard; flipped: boolean; onFlip: () => void }) {
  const { t, isFa, row } = useLang();
  const { colors, shadows } = useTheme();
  return (
    <Pressable onPress={onFlip} accessibilityRole="button">
      <View
        style={[
          {
            minHeight: 300,
            borderRadius: 22,
            padding: 20,
            justifyContent: "center",
            backgroundColor: flipped ? colors.cardBg : colors.accent,
          },
          shadows.raised,
        ]}
      >
        {flipped ? (
          <View style={{ gap: 10 }}>
            <AppText weight="900" size={18} style={{ marginBottom: 2 }}>
              {isFa ? card.front_fa : card.front_en}
            </AppText>
            {(isFa ? card.back_fields_fa : card.back_fields_en).map((block) => (
              <CardBackField key={block.field} block={block} row={row} />
            ))}
          </View>
        ) : (
          <View style={{ gap: 12 }}>
            <AppText weight="900" size={26} color={colors.onAccent} center>
              {isFa ? card.front_fa : card.front_en}
            </AppText>
            {isFa && card.front_en !== card.front_fa ? (
              <AppText weight="600" size={13} color={colors.onAccentSub} center style={{ marginTop: -6 }}>
                {card.front_en}
              </AppText>
            ) : null}
            {card.section_label_fa ? (
              <SectionChip label={isFa ? card.section_label_fa : card.section_label_en} tone={card.section_tone} onAccent />
            ) : null}
            <AppText weight="600" size={12} color={colors.onAccentSub} center>
              {t("cardsTapHint")}
            </AppText>
          </View>
        )}
      </View>
    </Pressable>
  );
}

function CategoryGrid({
  categories,
  topicsFinished,
  cardsReviewed,
  onOpen,
  onLeitner,
}: {
  categories: DeckCategory[];
  topicsFinished: number;
  cardsReviewed: number;
  onOpen: (key: string) => void;
  onLeitner: () => void;
}) {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  return (
    <Screen>
      <ScreenChrome title={t("cardsTitle")} help="flashcards" />
      <View style={[{ backgroundColor: colors.accent, borderRadius: 22, padding: 16, gap: 10 }, shadows.raisedSm]}>
        <AppText weight="600" size={13} color={colors.onAccentSub}>
          {isFa ? "یک دسته را باز کن و زیردسته‌ات را انتخاب کن." : "Open a category, then pick a topic."}
        </AppText>
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
          {[
            isFa ? `${n(topicsFinished)} زیردسته‌ی تمام‌شده` : `${topicsFinished} topics finished`,
            isFa ? `${n(cardsReviewed)} کارت مرورشده` : `${cardsReviewed} cards reviewed`,
          ].map((label) => (
            <View
              key={label}
              style={{
                backgroundColor: colors.onAccentChip,
                borderRadius: 999,
                paddingHorizontal: 12,
                paddingVertical: 5,
              }}
            >
              <AppText weight="700" size={12} color={colors.onAccent}>
                {label}
              </AppText>
            </View>
          ))}
        </View>
      </View>

      <Pressable
        onPress={onLeitner}
        accessibilityRole="button"
        style={{
          alignSelf: row === "row" ? "flex-start" : "flex-end",
          backgroundColor: colors.softBg,
          borderRadius: 999,
          paddingHorizontal: 14,
          paddingVertical: 8,
          marginVertical: spacing.md,
        }}
      >
        <AppText weight="800" size={12} color={colors.accent}>
          {t("leitnerShow")}
        </AppText>
      </Pressable>

      {categories.length === 0 ? (
        <Card>
          <AppText muted weight="600" size={13} center>
            {isFa ? "هنوز کارتی ساخته نشده است." : "No cards have been built yet."}
          </AppText>
        </Card>
      ) : (
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 12 }}>
          {categories.map((c) => {
            const started = c.topics.some((tp) => tp.position > 0 && !tp.finished);
            return (
              <Pressable
                key={c.key}
                onPress={() => onOpen(c.key)}
                accessibilityRole="button"
                style={[
                  {
                    width: "47.5%",
                    padding: 14,
                    gap: 8,
                    borderRadius: 20,
                    backgroundColor: colors.cardBg,
                    borderWidth: 2,
                    borderColor: started ? colors.accent : "transparent",
                  },
                  shadows.raisedSm,
                ]}
              >
                <IconImage name={iconFor(`cat-${c.key}`, "edu-flashcards")} size={44} />
                <AppText weight="800" size={14.5} numberOfLines={2}>
                  {isFa ? c.name_fa : c.name_en}
                </AppText>
                <AppText weight="600" size={12} muted>
                  {c.topics_finished > 0
                    ? isFa
                      ? `${n(c.topics_finished)} از ${n(c.topics.length)} زیردسته`
                      : `${c.topics_finished} of ${c.topics.length} topics`
                    : isFa
                      ? `${n(c.topics.length)} زیردسته`
                      : `${c.topics.length} topics`}
                </AppText>
                <ProgressBar value={c.topics.length ? c.topics_finished / c.topics.length : 0} />
              </Pressable>
            );
          })}
        </View>
      )}
    </Screen>
  );
}

function TopicList({
  category,
  onBack,
  onOpen,
}: {
  category: DeckCategory;
  onBack: () => void;
  onOpen: (topic: string) => void;
}) {
  const { isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  return (
    <Screen>
      <ScreenChrome title={isFa ? category.name_fa : category.name_en} onBack={onBack} />
      <View style={{ gap: 12 }}>
        {category.topics.map((tp) => {
          const inProgress = tp.position > 0 && !tp.finished;
          return (
            <Pressable
              key={tp.key}
              onPress={() => onOpen(tp.key)}
              accessibilityRole="button"
              style={[
                {
                  padding: 14,
                  gap: 10,
                  borderRadius: 20,
                  backgroundColor: colors.cardBg,
                  borderWidth: 2,
                  borderColor: inProgress ? colors.accent : "transparent",
                  opacity: tp.finished ? 0.78 : 1,
                },
                inProgress && shadows.raisedSm,
              ]}
            >
              <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
                <IconImage name={iconFor(`topic-${tp.key}`, "edu-flashcards")} size={40} />
                <View style={{ flex: 1, gap: 2 }}>
                  <AppText weight="800" size={15}>
                    {isFa ? tp.name_fa : tp.name_en}
                  </AppText>
                  <AppText weight="600" size={12} muted>
                    {tp.finished
                      ? isFa
                        ? `${n(tp.total)} کارت · مرور شد`
                        : `${tp.total} cards · reviewed`
                      : inProgress
                        ? isFa
                          ? `${n(tp.position)} از ${n(tp.total)} کارت`
                          : `${tp.position} of ${tp.total} cards`
                        : isFa
                          ? `${n(tp.total)} کارت`
                          : `${tp.total} cards`}
                  </AppText>
                </View>
                {tp.finished ? (
                  <View
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: 15,
                      backgroundColor: colors.accent,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <AppText weight="900" size={14} color={colors.onAccent}>
                      ✓
                    </AppText>
                  </View>
                ) : (
                  <View
                    style={{
                      paddingHorizontal: 13,
                      paddingVertical: 6,
                      borderRadius: 999,
                      backgroundColor: inProgress ? colors.accent : "transparent",
                    }}
                  >
                    <AppText weight="800" size={12.5} color={inProgress ? colors.onAccent : colors.accent}>
                      {inProgress ? (isFa ? "ادامه" : "Continue") : isFa ? "شروع" : "Start"}
                    </AppText>
                  </View>
                )}
              </View>
              {inProgress ? <ProgressBar value={tp.position / tp.total} height={6} /> : null}
            </Pressable>
          );
        })}
      </View>
    </Screen>
  );
}

/** One topic's deck, card by card in its fixed order, then the end screen. */
function TopicDeckView({
  topicKey,
  onBack,
  onHome,
  onNext,
}: {
  topicKey: string;
  onBack: () => void;
  onHome: () => void;
  onNext: (topic: string, category: string) => void;
}) {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const qc = useQueryClient();

  const deck = useQuery({ queryKey: ["flashcard-deck", topicKey], queryFn: () => flashcardsApi.deck(topicKey) });
  const [progress, setProgress] = useState<DeckProgress | null>(null);
  const [flipped, setFlipped] = useState(false);
  // This visit's cards not known (drug + section), for "review the hard
  // ones again" at the end; and whether the last answer boxed a card.
  const [hardKeys, setHardKeys] = useState<string[]>([]);
  const [boxed, setBoxed] = useState(false);
  const [reviewHard, setReviewHard] = useState<{ index: number } | null>(null);

  const current = progress ?? deck.data ?? null;

  const answer = useMutation({
    mutationFn: ({ card, rating }: { card: DeckCard; rating: "easy" | "hard" }) =>
      flashcardsApi.answer(topicKey, card.drug_slug, card.section, rating),
    onSuccess: (res, vars) => {
      setFlipped(false);
      setBoxed(vars.rating === "hard");
      if (reviewHard) {
        setReviewHard({ index: reviewHard.index + 1 });
      } else {
        setProgress(res);
        if (vars.rating === "hard") setHardKeys((h) => [...h, `${vars.card.drug_slug}/${vars.card.section}`]);
      }
      qc.invalidateQueries({ queryKey: ["flashcard-decks"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["leitner"] });
    },
  });
  const restart = useMutation({
    mutationFn: () => flashcardsApi.restart(topicKey),
    onSuccess: (res) => {
      setProgress(res);
      setHardKeys([]);
      setReviewHard(null);
      setFlipped(false);
      qc.invalidateQueries({ queryKey: ["flashcard-decks"] });
    },
  });

  if (deck.isLoading || !deck.data || !current) return <LoadingState />;

  const data = deck.data;
  const title = isFa ? data.name_fa : data.name_en;
  const hardCards = data.cards.filter((c) => hardKeys.includes(`${c.drug_slug}/${c.section}`));
  const reviewing = reviewHard && reviewHard.index < hardCards.length;
  const card = reviewing ? hardCards[reviewHard.index] : data.cards[current.position];
  const rate = (rating: "easy" | "hard") => card && answer.mutate({ card, rating });

  if (!card || (current.finished && !reviewing)) {
    const next = current.next_topic;
    return (
      <Screen>
        <ScreenChrome title={title} onBack={onBack} />
        <View style={{ alignItems: "center", gap: 10, paddingVertical: 8 }}>
          <IconImage name={iconFor(`topic-${data.key}`, "edu-flashcards")} size={72} />
          <AppText weight="900" size={22} center>
            {isFa ? `${title} تمام شد` : `${title}: done`}
          </AppText>
          <AppText weight="500" size={14} muted center>
            {isFa
              ? `هر ${n(current.total)} کارت این زیردسته را مرور کردی.`
              : `You've been through all ${current.total} cards in this topic.`}
          </AppText>
        </View>

        <View style={{ flexDirection: row, gap: 10, marginVertical: spacing.md }}>
          {[
            { value: current.known, label: t("cardEasy"), color: colors.accent },
            { value: current.hard, label: t("cardHard"), color: colors.denyLabel },
          ].map((s) => (
            <Card key={s.label} style={{ flex: 1, alignItems: "center" }}>
              <AppText weight="900" size={26} color={s.color}>
                {n(s.value)}
              </AppText>
              <AppText weight="700" size={12.5} muted>
                {s.label}
              </AppText>
            </Card>
          ))}
        </View>

        <View style={{ gap: 10 }}>
          {next ? (
            <Pressable
              onPress={() => onNext(next.key, next.category_key)}
              accessibilityRole="button"
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 12,
                padding: 14,
                borderRadius: 20,
                borderWidth: 2,
                borderColor: colors.accent,
                backgroundColor: colors.cardBg,
              }}
            >
              <IconImage name={iconFor(`topic-${next.key}`, "edu-flashcards")} size={40} />
              <View style={{ flex: 1 }}>
                <AppText weight="700" size={11.5} color={colors.accent2}>
                  {next.category_key === data.category_key
                    ? isFa
                      ? "زیردسته‌ی بعدی"
                      : "Next topic"
                    : isFa
                      ? `دسته‌ی بعدی: ${next.category_name_fa}`
                      : `Next category: ${next.category_name_en}`}
                </AppText>
                <AppText weight="800" size={15}>
                  {isFa ? next.name_fa : next.name_en}
                </AppText>
              </View>
              <AppText weight="900" size={18} color={colors.accent}>
                {isFa ? "‹" : "›"}
              </AppText>
            </Pressable>
          ) : null}
          {hardCards.length > 0 ? (
            <Button
              label={
                isFa
                  ? `مرور دوباره‌ی ${n(hardCards.length)} کارت سخت`
                  : `Review the ${hardCards.length} hard cards again`
              }
              variant="secondary"
              onPress={() => {
                setFlipped(false);
                setReviewHard({ index: 0 });
              }}
            />
          ) : null}
          <Button
            label={isFa ? "از اول" : "Start over"}
            variant="secondary"
            onPress={() => restart.mutate()}
            loading={restart.isPending}
          />
          <Button label={isFa ? "بازگشت به دسته‌ها" : "Back to categories"} variant="ghost" onPress={onHome} />
        </View>
      </Screen>
    );
  }

  const shown = reviewing ? reviewHard.index + 1 : current.position + 1;
  const total = reviewing ? hardCards.length : current.total;
  return (
    <Screen>
      <ScreenChrome title={title} onBack={reviewing ? () => setReviewHard(null) : onBack} />
      <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <AppText weight="700" size={12} muted>
          {reviewing ? (isFa ? "مرور کارت‌های سخت" : "Hard cards") : isFa ? data.category_name_fa : data.category_name_en}
        </AppText>
        <AppText weight="800" size={13} color={colors.accent}>
          {isFa ? `${n(shown)} از ${n(total)}` : `${shown} of ${total}`}
        </AppText>
      </View>
      <View style={{ marginBottom: spacing.md }}>
        <ProgressBar value={(shown - 1) / total} height={6} />
      </View>
      {boxed ? (
        <AppText weight="700" size={12} color={colors.accent} style={{ marginTop: -6, marginBottom: spacing.sm }}>
          {isFa ? "کارت قبلی به جعبهٔ لایتنر رفت." : "The last card went into the Leitner box."}
        </AppText>
      ) : null}

      <FlipCard card={card} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />

      {flipped ? (
        <View style={{ flexDirection: row, gap: 10, marginTop: spacing.lg }}>
          <Button
            label={t("cardHard")}
            variant="secondary"
            onPress={() => rate("hard")}
            disabled={answer.isPending}
            style={{ flex: 1 }}
          />
          <Button label={t("cardEasy")} onPress={() => rate("easy")} disabled={answer.isPending} style={{ flex: 1 }} />
        </View>
      ) : null}
    </Screen>
  );
}

export function FlashcardsScreen() {
  const params = useNav((s) => s.params);
  const [mode, setMode] = useState<Mode>(() =>
    params.leitner
      ? { kind: "leitner" }
      : typeof params.topic === "string"
        ? { kind: "deck", topic: params.topic, category: String(params.category ?? "") }
        : { kind: "categories" },
  );
  // Back steps out through the screen's own levels before leaving the tab.
  useBackInterceptor(mode.kind !== "categories", () =>
    setMode(mode.kind === "deck" ? { kind: "topics", category: mode.category } : { kind: "categories" }),
  );
  const decks = useQuery({ queryKey: ["flashcard-decks"], queryFn: flashcardsApi.decks, retry: false });
  const locked = decks.error instanceof ApiError && decks.error.status === 503;
  const { t } = useLang();

  if (mode.kind === "leitner") return <LeitnerBox onBack={() => setMode({ kind: "categories" })} />;
  if (decks.isLoading) return <LoadingState />;
  if (locked) {
    return (
      <Screen>
        <ScreenChrome title={t("cardsTitle")} help="flashcards" />
        <LockedCard />
      </Screen>
    );
  }

  const categories = decks.data?.categories ?? [];
  if (mode.kind === "deck") {
    return (
      <TopicDeckView
        key={mode.topic}
        topicKey={mode.topic}
        onBack={() => setMode(mode.category ? { kind: "topics", category: mode.category } : { kind: "categories" })}
        onHome={() => setMode({ kind: "categories" })}
        onNext={(topic, category) => setMode({ kind: "deck", topic, category })}
      />
    );
  }
  if (mode.kind === "topics") {
    const category = categories.find((c) => c.key === mode.category);
    if (category) {
      return (
        <TopicList
          category={category}
          onBack={() => setMode({ kind: "categories" })}
          onOpen={(topic) => setMode({ kind: "deck", topic, category: category.key })}
        />
      );
    }
  }
  return (
    <CategoryGrid
      categories={categories}
      topicsFinished={decks.data?.topics_finished ?? 0}
      cardsReviewed={decks.data?.cards_reviewed ?? 0}
      onOpen={(category) => setMode({ kind: "topics", category })}
      onLeitner={() => setMode({ kind: "leitner" })}
    />
  );
}
