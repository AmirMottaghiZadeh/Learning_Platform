import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { flashcardsApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

const BOX_LABEL_KEYS = ["leitnerL1", "leitnerL2", "leitnerL3", "leitnerL4", "leitnerL5"] as const;

export function FlashcardsScreen() {
  const { t, isFa, n } = useLang();
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
              <IconImage name="mobileBlister" size={34} />
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
          <Card key={b.box} style={{ marginBottom: spacing.sm, flexDirection: "row", alignItems: "center" }}>
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
      <ScreenChrome title={t("cardsTitle")} help="flashcards" />
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md }}>
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
                <AppText weight="500" size={14} style={{ lineHeight: 26 }}>
                  {isFa ? card.back_fa : card.back_en}
                </AppText>
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
            <View style={{ flexDirection: "row", gap: 10, marginTop: spacing.lg }}>
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
