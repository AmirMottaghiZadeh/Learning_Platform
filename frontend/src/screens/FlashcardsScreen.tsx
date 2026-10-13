import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { flashcardsApi } from "@/api/endpoints";
import { DeckCard, DeckCategory, DeckProgress, LeitnerCardField, SectionTone } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { ICONS, IconImage, IconName } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";

const BOX_LABEL_KEYS = ["leitnerL1", "leitnerL2", "leitnerL3", "leitnerL4", "leitnerL5"] as const;

/** Matches QuizScreen's chipColors: toneColors() leaves "info" transparent,
 * meant for a full section block rather than a small tag, so it needs its
 * own visible fill/border here too. */
function chipColors(tone: SectionTone, colors: ReturnType<typeof useTheme>["colors"]) {
  if (tone === "info") return { bg: colors.accent + "14", border: colors.accent, label: colors.accent };
  return toneColors(tone, colors);
}

/** One card section on the back: a heading in the section's own color
 * (the same tone vocabulary as the lesson screen and quiz tags) over its
 * facts, each its own bulleted line. */
function CardBackField({ block, row }: { block: LeitnerCardField; row: "row" | "row-reverse" }) {
  const { colors } = useTheme();
  const tag = chipColors(block.tone, colors);
  const items = block.items ?? block.text.split("\n").filter(Boolean);
  return (
    <View
      style={{
        backgroundColor: tag.bg,
        borderWidth: 1,
        borderColor: tag.border,
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingVertical: 9,
        gap: 4,
      }}
    >
      <View style={{ flexDirection: row, alignItems: "center", gap: 6 }}>
        <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: tag.label }} />
        <AppText weight="800" size={12.5} color={tag.label}>
          {block.label}
        </AppText>
      </View>
      {items.map((item, i) => (
        <View key={i} style={{ flexDirection: row, gap: 6 }}>
          <AppText weight="700" size={14} color={tag.label}>
            •
          </AppText>
          <AppText weight="500" size={14} style={{ flex: 1, lineHeight: 22 }}>
            {item}
          </AppText>
        </View>
      ))}
    </View>
  );
}

/** The spaced-repetition review: every Leitner card due today, across all
 * decks, plus the box summary. Reached from the deck browser. */
function LeitnerReview({ onBack }: { onBack: () => void }) {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const qc = useQueryClient();

  const [showBoxes, setShowBoxes] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const [cursor, setCursor] = useState(0);

  const due = useQuery({ queryKey: ["flashcards-due"], queryFn: flashcardsApi.due, retry: false });
  const boxes = useQuery({
    queryKey: ["flashcards-boxes"],
    queryFn: flashcardsApi.boxes,
    enabled: showBoxes,
    retry: false,
  });

  const locked = due.error instanceof ApiError && due.error.status === 503;

  const seed = useMutation({
    mutationFn: flashcardsApi.seed,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["flashcards-due"] }),
  });
  const review = useMutation({
    mutationFn: ({ id, rating }: { id: number; rating: "easy" | "hard" }) =>
      flashcardsApi.review(id, rating),
    onSuccess: () => {
      setFlipped(false);
      setCursor((c) => c + 1);
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (due.isLoading) return <LoadingState />;

  if (locked) {
    return (
      <Screen>
        <ScreenChrome title={t("cardsTitle")} help="flashcards" />
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
      </Screen>
    );
  }

  const cards = due.data ?? [];
  const card = cards[cursor];

  if (showBoxes) {
    return (
      <Screen>
        <ScreenChrome title={t("leitnerShow")} />
        <AppText muted weight="600" size={12} style={{ marginBottom: 16, lineHeight: 22 }}>
          {t("leitnerSub")}
        </AppText>
        {(boxes.data ?? []).map((b, i) => (
          <Card key={b.box} style={{ marginBottom: spacing.sm, flexDirection: row, alignItems: "center" }}>
            <View
              style={{
                width: 34,
                height: 34,
                borderRadius: 10,
                backgroundColor: colors.accent + "1a",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AppText weight="900" size={13} color={colors.accent}>
                {n(b.box)}
              </AppText>
            </View>
            <View style={{ flex: 1, marginHorizontal: 12 }}>
              <AppText weight="800" size={13}>
                {t(BOX_LABEL_KEYS[i] ?? "leitnerL1")}
              </AppText>
              <AppText muted weight="600" size={12}>
                {n(b.count)} {t("leitnerCards")}
              </AppText>
            </View>
            {b.due > 0 ? (
              <View
                style={{
                  backgroundColor: colors.leitnerActiveBg,
                  borderRadius: 999,
                  paddingHorizontal: 10,
                  paddingVertical: 4,
                }}
              >
                <AppText weight="800" size={11} color={colors.accent}>
                  {n(b.due)} {t("leitnerDueToday")}
                </AppText>
              </View>
            ) : null}
          </Card>
        ))}
        <Button
          label={t("leitnerHide")}
          variant="secondary"
          onPress={() => setShowBoxes(false)}
          style={{ marginTop: spacing.md }}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <ScreenChrome title={t("leitnerShow")} onBack={onBack} />
      <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md }}>
        <Pressable
          onPress={() => setShowBoxes(true)}
          style={{
            backgroundColor: colors.softBg,
            borderRadius: 999,
            paddingHorizontal: 12,
            paddingVertical: 7,
          }}
        >
          <AppText weight="800" size={12} color={colors.accent}>
            {t("leitnerShow")}
          </AppText>
        </Pressable>
        <AppText weight="800" size={12} muted>
          {cards.length ? `${n(Math.min(cursor + 1, cards.length))}/${n(cards.length)}` : ""}
        </AppText>
      </View>

      {cards.length === 0 ? (
        <Card>
          <View style={{ alignItems: "center", gap: 12, paddingVertical: 20 }}>
            <AppText weight="800" size={15}>
              {t("cardsDoneTitle")}
            </AppText>
            <AppText muted weight="600" size={13} center>
              {t("cardsDoneSub")}
            </AppText>
            <Button label={t("leitnerStartBtn")} onPress={() => seed.mutate()} loading={seed.isPending} />
          </View>
        </Card>
      ) : !card ? (
        <Card>
          <AppText weight="800" size={15} center>
            {t("cardsDoneTitle")}
          </AppText>
          <AppText muted weight="600" size={13} center style={{ marginTop: 6 }}>
            {t("cardsDoneSub")}
          </AppText>
        </Card>
      ) : (
        <>
          <Pressable onPress={() => setFlipped((f) => !f)}>
            <View
              style={[
                {
                  minHeight: 260,
                  borderRadius: 20,
                  padding: 22,
                  justifyContent: "center",
                  backgroundColor: flipped ? colors.cardBg : colors.accent,
                },
                shadows.raised,
              ]}
            >
              {flipped ? (
                <View style={{ gap: 14 }}>
                  {(isFa ? card.back_fields_fa : card.back_fields_en).map((block) => (
                    <CardBackField key={block.field} block={block} row={row} />
                  ))}
                </View>
              ) : (
                <>
                  <AppText weight="900" size={24} color="#fff" center>
                    {isFa ? card.front_fa : card.front_en}
                  </AppText>
                  <AppText weight="600" size={12} color="rgba(255,255,255,0.75)" center style={{ marginTop: 10 }}>
                    {t("cardsTapHint")}
                  </AppText>
                </>
              )}
            </View>
          </Pressable>

          {flipped ? (
            <View style={{ flexDirection: row, gap: 10, marginTop: spacing.lg }}>
              <Button
                label={t("cardHard")}
                variant="secondary"
                onPress={() => review.mutate({ id: card.id, rating: "hard" })}
                style={{ flex: 1 }}
              />
              <Button
                label={t("cardEasy")}
                onPress={() => review.mutate({ id: card.id, rating: "easy" })}
                style={{ flex: 1 }}
              />
            </View>
          ) : null}
        </>
      )}
    </Screen>
  );
}

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

/** The card itself: drug name on the front, the colored sections on the back. */
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
          <>
            <AppText weight="900" size={26} color={colors.onAccent} center>
              {isFa ? card.front_fa : card.front_en}
            </AppText>
            <AppText weight="600" size={12} color={colors.onAccentSub} center style={{ marginTop: 10 }}>
              {t("cardsTapHint")}
            </AppText>
          </>
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
                        ? `${n(tp.total)} دارو · مرور شد`
                        : `${tp.total} drugs · reviewed`
                      : inProgress
                        ? isFa
                          ? `${n(tp.position)} از ${n(tp.total)} دارو`
                          : `${tp.position} of ${tp.total} drugs`
                        : isFa
                          ? `${n(tp.total)} دارو`
                          : `${tp.total} drugs`}
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
  // This visit's hard cards, for "review the hard ones again" at the end.
  const [hardSlugs, setHardSlugs] = useState<string[]>([]);
  const [reviewHard, setReviewHard] = useState<{ index: number } | null>(null);

  const current = progress ?? deck.data ?? null;

  const answer = useMutation({
    mutationFn: ({ slug, rating }: { slug: string; rating: "easy" | "hard" }) =>
      flashcardsApi.answer(topicKey, slug, rating),
    onSuccess: (res, vars) => {
      setFlipped(false);
      if (reviewHard) {
        setReviewHard({ index: reviewHard.index + 1 });
      } else {
        setProgress(res);
        if (vars.rating === "hard") setHardSlugs((h) => [...h, vars.slug]);
      }
      qc.invalidateQueries({ queryKey: ["flashcard-decks"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const restart = useMutation({
    mutationFn: () => flashcardsApi.restart(topicKey),
    onSuccess: (res) => {
      setProgress(res);
      setHardSlugs([]);
      setReviewHard(null);
      setFlipped(false);
      qc.invalidateQueries({ queryKey: ["flashcard-decks"] });
    },
  });

  if (deck.isLoading || !deck.data || !current) return <LoadingState />;

  const data = deck.data;
  const title = isFa ? data.name_fa : data.name_en;
  const hardCards = data.cards.filter((c) => hardSlugs.includes(c.drug_slug));
  const reviewing = reviewHard && reviewHard.index < hardCards.length;
  const card = reviewing ? hardCards[reviewHard.index] : data.cards[current.position];
  const rate = (rating: "easy" | "hard") => card && answer.mutate({ slug: card.drug_slug, rating });

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
              ? `هر ${n(current.total)} داروی این زیردسته را مرور کردی.`
              : `You've been through all ${current.total} drugs in this topic.`}
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
  const [mode, setMode] = useState<Mode>({ kind: "categories" });
  const decks = useQuery({ queryKey: ["flashcard-decks"], queryFn: flashcardsApi.decks, retry: false });
  const locked = decks.error instanceof ApiError && decks.error.status === 503;
  const { t } = useLang();

  if (mode.kind === "leitner") return <LeitnerReview onBack={() => setMode({ kind: "categories" })} />;
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
        onBack={() => setMode({ kind: "topics", category: mode.category })}
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
