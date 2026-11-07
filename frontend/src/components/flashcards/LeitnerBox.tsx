import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { flashcardsApi } from "@/api/endpoints";
import { BoxCard, BoxRating, LeitnerOverview, RatingOutcome } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { CardBackField, SectionChip } from "@/components/flashcards/CardParts";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { spacing } from "@/theme/tokens";

export const LEITNER_KEY = ["leitner"];

// The drawers widen from 1 to 5, as in a real Leitner box.
const DRAWER_FLEX = [1, 1.08, 1.16, 1.24, 1.32];
const STACK_LINES_MAX = 22;

/** Where the button sends the card: "به کشوی ۴", or out of the box. When it
 * comes back is the scheduler's business, never shown as days. */
function outcomeLabel(o: RatingOutcome | undefined, isFa: boolean, n: (v: number) => string) {
  if (!o) return "";
  if (o.box === 0) return isFa ? "خروج از جعبه" : "Leaves the box";
  return isFa ? `به کشوی ${n(o.box)}` : `To drawer ${o.box}`;
}

/** The Leitner box: the cards the learner did not know, in five drawers by
 * how often each was missed, and today's review. Reached from the
 * flashcards tab (or a study-plan task); `onBack` leaves it. */
export function LeitnerBox({ onBack }: { onBack: () => void }) {
  // null: the drawers; 0: today's review; 1-5: one drawer's cards
  const [session, setSession] = useState<number | null>(null);
  useBackInterceptor(session !== null, () => setSession(null));
  if (session !== null) return <ReviewSession box={session || undefined} onDone={() => setSession(null)} />;
  return <Drawers onBack={onBack} onReview={setSession} />;
}

function Drawers({ onBack, onReview }: { onBack: () => void; onReview: (box: number) => void }) {
  const { isFa, n, row } = useLang();
  const { colors } = useTheme();
  const { data, isLoading } = useQuery({ queryKey: LEITNER_KEY, queryFn: flashcardsApi.leitner, staleTime: 0, refetchOnMount: "always" });
  useTour("leitner", !!data);

  if (isLoading || !data) return <LoadingState />;
  const title = isFa ? "جعبهٔ لایتنر" : "Leitner box";
  return (
    <Screen>
      <ScreenChrome title={title} onBack={onBack} tour="leitner" />
      <AppText weight="700" size={12.5} muted style={{ marginTop: -6, marginBottom: spacing.md }}>
        {isFa ? `${n(data.total)} کارت در ۵ کشو` : `${data.total} cards in 5 drawers`}
      </AppText>

      <TourTarget id="leitner.drawers">
      <View style={{ borderRadius: 20, backgroundColor: colors.trackBg, padding: 10 }}>
        <View style={{ flexDirection: row, gap: 6 }}>
          {data.drawers.map((d, i) => (
            <Pressable
              key={d.box}
              onPress={d.count ? () => onReview(d.box) : undefined}
              disabled={!d.count}
              accessibilityRole="button"
              accessibilityLabel={isFa ? `کشوی ${n(d.box)}، ${n(d.count)} کارت` : `Drawer ${d.box}, ${d.count} cards`}
              style={({ pressed }) => ({ flex: DRAWER_FLEX[i], gap: 8, opacity: pressed ? 0.8 : 1 })}
            >
              <View
                style={{
                  height: 170,
                  borderRadius: 12,
                  backgroundColor: colors.softBg,
                  paddingHorizontal: 6,
                  paddingTop: 8,
                  paddingBottom: 6,
                  justifyContent: "flex-end",
                }}
              >
                <AppText weight="800" size={12} muted center style={{ marginBottom: 4 }}>
                  {n(d.count)}
                </AppText>
                {d.due ? (
                  <View
                    style={{
                      alignSelf: "center",
                      paddingHorizontal: 7,
                      paddingVertical: 1,
                      borderTopLeftRadius: 7,
                      borderTopRightRadius: 7,
                      backgroundColor: colors.accent,
                    }}
                  >
                    <AppText weight="800" size={10.5} color={colors.onAccent}>
                      {n(d.due)}
                    </AppText>
                  </View>
                ) : null}
                {/* the stack of cards: one edge a card, up to a point */}
                {d.count ? (
                  <View
                    style={{
                      borderRadius: 5,
                      borderWidth: 1,
                      borderColor: colors.trackBg,
                      backgroundColor: colors.cardBg,
                      overflow: "hidden",
                    }}
                  >
                    {Array.from({ length: Math.min(d.count, STACK_LINES_MAX) }, (_, k) => (
                      <View key={k} style={{ height: 5, borderTopWidth: k ? 1 : 0, borderTopColor: colors.trackBg }} />
                    ))}
                  </View>
                ) : null}
              </View>
              <AppText weight="900" size={16} center>
                {n(d.box)}
              </AppText>
            </Pressable>
          ))}
        </View>
      </View>
      </TourTarget>

      <View style={{ gap: 6, marginTop: spacing.md, marginBottom: spacing.lg }}>
        <View style={{ flexDirection: row, alignItems: "center", gap: 6 }}>
          <View style={{ width: 14, height: 8, borderTopLeftRadius: 3, borderTopRightRadius: 3, backgroundColor: colors.accent }} />
          <AppText weight="700" size={11.5} muted>
            {isFa ? "زبانهٔ سبز: کارت‌هایی که امروز نوبتشان است" : "Green tab: cards due today"}
          </AppText>
        </View>
        <AppText weight="600" size={11.5} muted style={{ lineHeight: 19 }}>
          {isFa
            ? "شمارهٔ کشو یعنی چند بار اشتباه شده. «یادم بود» کارت را یک کشو پایین می‌آورد و از کشوی ۱ بیرون می‌برد."
            : "A drawer's number is how often its cards were missed. “I knew it” moves a card down a drawer, and out from drawer 1."}
        </AppText>
      </View>

      <TourTarget id="leitner.today">
        <TodayCard data={data} onStart={() => onReview(0)} />
      </TourTarget>
      {data.exam_days_left != null ? (
        <AppText weight="700" size={12} color={colors.accent} style={{ marginTop: spacing.md }}>
          {isFa
            ? `آزمون ${n(data.exam_days_left)} روز دیگر است؛ فاصله‌های مرور تا آن روز فشرده شده‌اند.`
            : `The exam is in ${data.exam_days_left} days; review gaps are shortened to fit.`}
        </AppText>
      ) : null}
    </Screen>
  );
}

function TodayCard({ data, onStart }: { data: LeitnerOverview; onStart: () => void }) {
  const { isFa, n, row } = useLang();
  const { colors } = useTheme();

  let note: string | null = null;
  if (!data.total)
    note = isFa
      ? "هنوز کارتی در جعبه نیست. هر کارتی که در فلش‌کارت «یادم نبود» بزنی یا در آزمون اشتباه جواب بدهی، اینجا می‌آید."
      : "The box is empty. Any card you mark “I didn't know” in flashcards, or get wrong in a quiz, comes here.";
  else if (!data.today && data.due)
    note = isFa
      ? `سقف امروز (${n(data.daily_minutes)} دقیقه) پر شد. بقیه فردا می‌آیند.`
      : `Today's ${data.daily_minutes} minutes are used up. The rest come tomorrow.`;
  else if (!data.today)
    note = isFa ? "امروز کارتی برای مرور نمانده." : "No cards left to review today.";

  return (
    <Card padded={false} style={{ overflow: "hidden" }}>
      <View
        style={{
          flexDirection: row,
          justifyContent: "space-between",
          alignItems: "baseline",
          backgroundColor: colors.accent,
          paddingHorizontal: spacing.lg,
          paddingVertical: 12,
        }}
      >
        <AppText weight="900" size={15} color={colors.onAccent}>
          {isFa ? `مرور امروز: ${n(data.today)} کارت` : `Today: ${data.today} cards`}
        </AppText>
        {data.today ? (
          <AppText weight="700" size={12} color={colors.onAccentSub}>
            {isFa ? `حدود ${n(data.today_minutes)} دقیقه` : `about ${data.today_minutes} min`}
          </AppText>
        ) : null}
      </View>
      <View style={{ padding: spacing.lg, gap: 8 }}>
        {data.preview.map((c) => (
          <View key={c.id} style={{ flexDirection: row, justifyContent: "space-between", gap: 8 }}>
            <AppText weight="700" size={12.5} style={{ flex: 1 }} numberOfLines={1}>
              {isFa ? `${c.front_fa}، ${c.section_label_fa}` : `${c.front_en}, ${c.section_label_en}`}
            </AppText>
            <AppText weight="700" size={12} muted>
              {isFa ? `کشوی ${n(c.box)}` : `Drawer ${c.box}`}
            </AppText>
          </View>
        ))}
        {note ? (
          <AppText weight="600" size={13} muted style={{ lineHeight: 21 }}>
            {note}
          </AppText>
        ) : null}
        {data.today ? <Button label={isFa ? "شروع مرور" : "Start the review"} onPress={onStart} style={{ marginTop: 4 }} /> : null}
      </View>
    </Card>
  );
}

const RATING_BUTTONS: { rating: BoxRating; fa: string; en: string }[] = [
  { rating: "forgot", fa: "یادم نبود", en: "I didn't know" },
  { rating: "good", fa: "یادم بود", en: "I knew it" },
];

/** A review: today's cards, or one drawer's (`box`). A card answered
 * "یادم نبود" climbs a drawer and comes round again at the end of the same
 * session. */
function ReviewSession({ box, onDone }: { box?: number; onDone: () => void }) {
  const { isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["leitner-cards", box ?? "today"],
    queryFn: () => flashcardsApi.leitnerCards(box),
    staleTime: 0,
    gcTime: 0,
  });
  const [extra, setExtra] = useState<BoxCard[]>([]);
  const [cursor, setCursor] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [stats, setStats] = useState({ reviewed: 0, out: 0 });

  const review = useMutation({
    mutationFn: ({ card, rating }: { card: BoxCard; rating: BoxRating }) => flashcardsApi.leitnerReview(card.id, rating),
    onSuccess: (updated, { rating }) => {
      if (rating === "forgot") setExtra((e) => [...e, updated]);
      setStats((s) => ({ reviewed: s.reviewed + 1, out: s.out + (updated.box === 0 ? 1 : 0) }));
      setFlipped(false);
      setCursor((c) => c + 1);
      qc.invalidateQueries({ queryKey: LEITNER_KEY });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["plan-today-brief"] });
    },
  });

  if (isLoading || !data) return <LoadingState />;
  const queue = [...data, ...extra];
  const card = queue[cursor];
  const title = box ? (isFa ? `کشوی ${n(box)}` : `Drawer ${box}`) : isFa ? "مرور امروز" : "Today's review";

  if (!card) {
    return (
      <Screen>
        <ScreenChrome title={title} onBack={onDone} />
        <Card style={{ alignItems: "center", gap: 8, paddingVertical: 28 }}>
          <AppText weight="900" size={20} center>
            {stats.reviewed ? (isFa ? "مرور تمام شد" : "Review done") : isFa ? "کارتی نمانده" : "No cards left"}
          </AppText>
          {stats.reviewed ? (
            <AppText weight="600" size={13.5} muted center style={{ lineHeight: 22 }}>
              {isFa
                ? `${n(stats.reviewed)} کارت مرور شد${stats.out ? `، ${n(stats.out)} کارت از جعبه بیرون رفت` : ""}.`
                : `${stats.reviewed} cards reviewed${stats.out ? `, ${stats.out} left the box` : ""}.`}
            </AppText>
          ) : null}
          <Button label={isFa ? "بازگشت به جعبه" : "Back to the box"} onPress={onDone} style={{ marginTop: 10 }} />
        </Card>
      </Screen>
    );
  }

  const back = isFa ? card.back_fields_fa : card.back_fields_en;
  return (
    <Screen>
      <ScreenChrome title={title} onBack={onDone} />
      <View style={{ flexDirection: row, justifyContent: "space-between", marginBottom: 6 }}>
        <AppText weight="700" size={12} muted>
          {isFa ? `کشوی ${n(card.box)}` : `Drawer ${card.box}`}
        </AppText>
        <AppText weight="800" size={12.5} color={colors.accent}>
          {isFa ? `${n(cursor + 1)} از ${n(queue.length)}` : `${cursor + 1} of ${queue.length}`}
        </AppText>
      </View>
      <View style={{ height: 6, borderRadius: 3, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row, marginBottom: spacing.md }}>
        <View style={{ width: `${(cursor / queue.length) * 100}%`, backgroundColor: colors.accent, borderRadius: 3 }} />
      </View>

      <Pressable onPress={() => setFlipped((f) => !f)} accessibilityRole="button">
        <View
          style={[
            {
              minHeight: 300,
              borderRadius: 22,
              padding: 20,
              justifyContent: "center",
              gap: 12,
              backgroundColor: flipped ? colors.cardBg : colors.accent,
            },
            shadows.raised,
          ]}
        >
          {flipped ? (
            <>
              <AppText weight="900" size={18}>
                {isFa ? card.front_fa : card.front_en}
              </AppText>
              {back.map((block) => (
                <CardBackField key={block.field} block={block} row={row} />
              ))}
            </>
          ) : (
            <>
              <AppText weight="900" size={26} color={colors.onAccent} center>
                {isFa ? card.front_fa : card.front_en}
              </AppText>
              {isFa && card.front_en !== card.front_fa ? (
                <AppText weight="600" size={13} color={colors.onAccentSub} center>
                  {card.front_en}
                </AppText>
              ) : null}
              <SectionChip label={isFa ? card.section_label_fa : card.section_label_en} tone={card.section_tone} onAccent />
              <AppText weight="600" size={12} color={colors.onAccentSub} center>
                {isFa ? "برای دیدن جواب لمس کن" : "Tap to see the answer"}
              </AppText>
            </>
          )}
        </View>
      </Pressable>

      {flipped ? (
        <View style={{ flexDirection: row, gap: 8, marginTop: spacing.lg }}>
          {RATING_BUTTONS.map(({ rating, fa, en }) => {
            const primary = rating === "good";
            return (
              <Pressable
                key={rating}
                onPress={() => review.mutate({ card, rating })}
                disabled={review.isPending}
                accessibilityRole="button"
                style={({ pressed }) => ({
                  flex: 1,
                  height: 64,
                  borderRadius: 16,
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 2,
                  backgroundColor: primary ? colors.accent : colors.denyBg,
                  borderWidth: primary ? 0 : 1.5,
                  borderColor: colors.denyBorder,
                  opacity: pressed || review.isPending ? 0.7 : 1,
                })}
              >
                <AppText weight="900" size={15} color={primary ? colors.onAccent : colors.denyInk}>
                  {isFa ? fa : en}
                </AppText>
                <AppText weight="700" size={11.5} color={primary ? colors.onAccentSub : colors.denyLabel}>
                  {outcomeLabel(card.outcomes[rating], isFa, n)}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </Screen>
  );
}
