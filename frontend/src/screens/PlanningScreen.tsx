import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { PlanItemActivity, StudyPlanItem } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

const ACTIVITY_LABEL: Record<PlanItemActivity, StringKey> = {
  lesson: "planningActivityLesson",
  quiz: "planningActivityQuiz",
  flashcards: "planningActivityFlashcards",
  mistake_review: "planningActivityMistakeReview",
};

/** The planner's home: "what do I do right now" (see the planning spec's UX
 * rule this implements), not a calendar. Free-study users see an empty
 * state with a way to build a plan; goal/maintenance users see today's
 * queue, fed by GET /me/plan/today/ which also lazily (re)generates a
 * maintenance plan's pick for the day. */
export function PlanningScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);
  const qc = useQueryClient();

  const { data: plan, isLoading: planLoading } = useQuery({ queryKey: ["plan"], queryFn: meApi.plan });
  const hasActivePlan = !!plan && plan.mode !== "none";
  const { data: today, isLoading: todayLoading } = useQuery({
    queryKey: ["plan-today"],
    queryFn: meApi.planToday,
    enabled: hasActivePlan,
  });

  const complete = useMutation({
    mutationFn: (id: number) => meApi.completePlanItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan-today"] }),
  });
  const skip = useMutation({
    mutationFn: (id: number) => meApi.skipPlanItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan-today"] }),
  });

  const openActivity = (item: StudyPlanItem) => {
    if (item.activity_type === "lesson" && item.atc_code) navigate("lessonList", { code: item.atc_code });
    else if (item.activity_type === "mistake_review") navigate("mistakes");
    else if (item.activity_type === "quiz") setTab("quiz");
    else if (item.activity_type === "flashcards") setTab("flashcards");
  };

  if (planLoading) return <LoadingState />;

  if (!hasActivePlan) {
    return (
      <Screen>
        <ScreenChrome title={t("planningTitle")} onBack={goBack} help="planning" />
        <Card style={{ alignItems: "center", paddingVertical: 30 }}>
          <AppText weight="800" size={15} center style={{ marginBottom: 8 }}>
            {t("planningEmptyTitle")}
          </AppText>
          <AppText muted weight="600" size={13} center style={{ marginBottom: 20, lineHeight: 20, maxWidth: 280 }}>
            {t("planningEmptyBody")}
          </AppText>
          <Pressable
            onPress={() => navigate("planningSetup")}
            style={[
              {
                backgroundColor: colors.accent,
                borderRadius: 14,
                paddingVertical: 13,
                paddingHorizontal: 26,
              },
              shadows.glow,
            ]}
          >
            <AppText weight="800" size={14} color={colors.onAccent}>
              {t("planningCreateCta")}
            </AppText>
          </Pressable>
        </Card>
      </Screen>
    );
  }

  if (todayLoading || !today) return <LoadingState />;

  const pending = today.items.filter((i) => i.status === "pending");
  const resolved = today.items.filter((i) => i.status !== "pending");
  const doneCount = today.items.filter((i) => i.status === "done").length;

  return (
    <Screen>
      <ScreenChrome title={t("planningTitle")} onBack={goBack} help="planning" />

      <Pressable
        onPress={() => navigate("planningSetup")}
        style={{ alignSelf: isFa ? "flex-start" : "flex-end", marginBottom: spacing.md }}
      >
        <AppText weight="700" size={12} color={colors.accent}>
          {t("planningEditPlan")}
        </AppText>
      </Pressable>

      <Card style={{ marginBottom: spacing.lg }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <AppText weight="900" size={20}>
            {n(doneCount)}/{n(today.items.length)}
          </AppText>
          <AppText muted weight="700" size={12}>
            {n(today.total_minutes)} {t("planningTodayMinutes")}
          </AppText>
        </View>
        <View
          style={{
            height: 6,
            borderRadius: 3,
            backgroundColor: colors.trackBg,
            marginTop: 10,
            overflow: "hidden",
          }}
        >
          <View
            style={{
              width: `${today.items.length ? Math.max(3, Math.round((doneCount / today.items.length) * 100)) : 0}%`,
              height: 6,
              backgroundColor: colors.accent,
            }}
          />
        </View>
      </Card>

      {today.topics.length ? (
        <View style={{ marginBottom: spacing.lg }}>
          <AppText weight="800" size={13} muted style={{ marginBottom: 8 }}>
            {t("planningTopicsHeading")}
          </AppText>
          <View style={{ gap: 8 }}>
            {today.topics.map((topic) => (
              <View
                key={topic.key}
                style={{
                  flexDirection: row,
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: colors.softBg,
                  borderRadius: 12,
                  paddingVertical: 9,
                  paddingHorizontal: 12,
                }}
              >
                <AppText weight="700" size={13} style={{ flex: 1 }}>
                  {isFa ? topic.name_fa : topic.name_en}
                </AppText>
                <AppText muted size={11} weight="700">
                  {t("planningProgressLabel")} {n(topic.progress_pct)}%
                </AppText>
                <AppText muted size={11} weight="700" style={{ marginLeft: 10 }}>
                  {t("planningMasteryLabel")} {n(topic.mastery_pct)}%
                </AppText>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {pending.length === 0 ? (
        <Card style={{ alignItems: "center", paddingVertical: 26, marginBottom: spacing.lg }}>
          <AppText weight="800" size={14} center style={{ marginBottom: 6 }}>
            {t("planningAllDoneTitle")}
          </AppText>
          <AppText muted weight="600" size={12} center>
            {t("planningAllDoneBody")}
          </AppText>
        </Card>
      ) : (
        <View style={{ gap: 10, marginBottom: spacing.lg }}>
          {pending.map((item, i) => (
            <PlanItemRow
              key={item.id}
              item={item}
              label={i === 0 ? t("planningNowLabel") : t("planningNextLabel")}
              onOpen={() => openActivity(item)}
              onComplete={() => complete.mutate(item.id)}
              onSkip={() => skip.mutate(item.id)}
            />
          ))}
        </View>
      )}

      {resolved.length ? (
        <View style={{ gap: 8 }}>
          <AppText weight="800" size={12} muted>
            {t("planningDoneSectionLabel")}
          </AppText>
          {resolved.map((item) => (
            <View
              key={item.id}
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 10,
                backgroundColor: colors.softBg,
                borderRadius: 12,
                padding: 10,
                opacity: 0.6,
              }}
            >
              <AppText
                weight="700"
                size={12}
                style={{ flex: 1, textDecorationLine: item.status === "done" ? "line-through" : "none" }}
              >
                {t(ACTIVITY_LABEL[item.activity_type])}
              </AppText>
              <AppText muted size={11} weight="700">
                {item.status === "done" ? "✓" : "–"}
              </AppText>
            </View>
          ))}
        </View>
      ) : null}
    </Screen>
  );
}

function PlanItemRow({
  item,
  label,
  onOpen,
  onComplete,
  onSkip,
}: {
  item: StudyPlanItem;
  label: string;
  onOpen: () => void;
  onComplete: () => void;
  onSkip: () => void;
}) {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();

  return (
    <View
      style={[
        { backgroundColor: colors.cardBg, borderRadius: 16, padding: 13, gap: 10 },
        shadows.raisedSm,
      ]}
    >
      <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
        <AppText weight="800" size={11} color={colors.accent}>
          {label}
        </AppText>
        <AppText muted weight="700" size={11}>
          {n(item.estimated_minutes)} {isFa ? "دقیقه" : "min"}
        </AppText>
      </View>
      <AppText weight="800" size={14}>
        {t(ACTIVITY_LABEL[item.activity_type])}
      </AppText>
      {item.reason_fa || item.reason_en ? (
        <AppText muted weight="600" size={12} style={{ lineHeight: 18 }}>
          {isFa ? item.reason_fa : item.reason_en}
        </AppText>
      ) : null}
      <View style={{ flexDirection: row, gap: 8, marginTop: 2 }}>
        <Pressable
          onPress={onOpen}
          style={{
            flex: 1,
            backgroundColor: colors.accent,
            borderRadius: 11,
            paddingVertical: 11,
            alignItems: "center",
          }}
        >
          <AppText weight="800" size={12.5} color={colors.onAccent}>
            {t("planningStartActivity")}
          </AppText>
        </Pressable>
        <Pressable
          onPress={onComplete}
          style={{
            paddingVertical: 11,
            paddingHorizontal: 14,
            borderRadius: 11,
            backgroundColor: colors.softBg,
          }}
        >
          <AppText weight="800" size={12.5}>
            {t("planningMarkDone")}
          </AppText>
        </Pressable>
        <Pressable
          onPress={onSkip}
          style={{
            paddingVertical: 11,
            paddingHorizontal: 14,
            borderRadius: 11,
            backgroundColor: colors.softBg,
          }}
        >
          <AppText muted weight="800" size={12.5}>
            {t("planningSkip")}
          </AppText>
        </Pressable>
      </View>
    </View>
  );
}
