import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { AtcPlanActivity, StudyPlanItem } from "@/api/types";
import { PLAN_BRIEF_KEY } from "@/components/plan/PlanSection";
import { STUDY_TILES } from "@/components/HomeTileGrid";
import { Button } from "@/components/primitives/Button";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Chevron } from "@/components/primitives/Chevron";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_SHORT } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function PlanningScreen() {
  const { t, isFa, lang, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const qc = useQueryClient();

  const firstActivity = useNav((s) => s.params.firstActivity) as AtcPlanActivity | null | undefined;
  const planQuery = useQuery({ queryKey: ["plan"], queryFn: meApi.plan, retry: false });
  const plan = planQuery.data;
  const hasActivePlan = plan?.mode === "goal";
  const todayQuery = useQuery({
    queryKey: ["plan-today"],
    queryFn: meApi.planToday,
    enabled: hasActivePlan,
    retry: false,
  });
  const today = todayQuery.data;
  const refreshPlan = () => {
    void qc.invalidateQueries({ queryKey: ["plan-today"] });
    void qc.invalidateQueries({ queryKey: PLAN_BRIEF_KEY });
  };

  const complete = useMutation({
    mutationFn: (id: number) => meApi.completePlanItem(id),
    onSuccess: refreshPlan,
  });
  const skip = useMutation({
    mutationFn: (id: number) => meApi.skipPlanItem(id),
    onSuccess: refreshPlan,
  });

  const openActivity = (item: StudyPlanItem) => {
    if (item.activity_type === "lesson" && item.atc_code) navigate("lessonList", { code: item.atc_code, studyPlan: !!plan?.atc_groups?.length });
    else if (item.activity_type === "mistake_review") navigate("mistakes");
    else if (item.activity_type === "quiz" && item.atc_code) navigate("quiz", { planChapter: item.atc_code, planTitle: isFa ? item.title_fa : item.title_en });
    else if (item.activity_type === "quiz") navigate("quiz", { topic: item.topic_key });
    else if (item.activity_type === "lesson") navigate("lessons");
  };

  const header = <ScreenChrome title={t("planningTitle")} onBack={goBack} help="planning" />;
  const learningPath = (
    <Card testID="student-learning-path" style={{ gap: spacing.sm }}>
      <AppText accessibilityRole="header" size={16} weight="800">{isFa ? "ترتیب مطالعه" : "Study sequence"}</AppText>
      {STUDY_TILES.map(({ label, screen }, i) => (
        <Pressable key={label} accessibilityLabel={t(label)} accessibilityRole="button"
          accessibilityState={{ disabled: !screen }} disabled={!screen} onPress={screen ? () => navigate(screen) : undefined}
          style={({ pressed }) => ({
            flexDirection: row, minHeight: 52, alignItems: "center", gap: spacing.sm,
            padding: spacing.sm, borderRadius: 10, backgroundColor: colors.softBg, opacity: pressed ? 0.76 : 1,
          })}>
          <AppText color={colors.accent} weight="800" center size={13} style={{ minWidth: 25 }}>{n(i + 1)}</AppText>
          <AppText size={14} weight="700" muted={!screen} style={{ flex: 1 }}>{t(label)}</AppText>
          {screen ? <Chevron /> : <AppText size={11} muted>{t("comingSoon")}</AppText>}
        </Pressable>
      ))}
    </Card>
  );
  const planError = planQuery.isError || (hasActivePlan && todayQuery.isError);
  if (!today || !hasActivePlan || planError) {
    return (
      <Screen contentStyle={{ maxWidth: 790, gap: spacing.md }} keyboardShouldPersistTaps="handled">
        {header}
        {learningPath}
        {planQuery.isPending || (hasActivePlan && todayQuery.isPending) ? <LoadingState /> : null}
        {planError ? <Card style={{ gap: spacing.sm }}>
          <AppText accessibilityRole="alert" muted>{t("loadFailed")}</AppText>
          <Button label={t("retry")} variant="secondary" onPress={() => void (planQuery.isError ? planQuery.refetch() : todayQuery.refetch())} />
        </Card> : null}
        {planQuery.isSuccess && !hasActivePlan ? (
          <Card style={{ gap: spacing.sm }}>
            <AppText weight="900" size={18}>{t("planningEmptyTitle")}</AppText>
            <AppText muted size={13}>{t("planningEmptyBody")}</AppText>
            <Button label={t("planningCreateCta")} full={false} onPress={() => navigate("planningSetup")} />
          </Card>
        ) : null}
      </Screen>
    );
  }

  const pending = today.items.filter((item) => item.status === "pending");
  const resolved = today.items.filter((item) => item.status !== "pending");
  const doneCount = today.items.filter((item) => item.status === "done").length;
  const pct = today.items.length ? Math.round((doneCount / today.items.length) * 100) : 0;

  return (
    <Screen contentStyle={{ maxWidth: 790, gap: spacing.md }}>
      {header}
      {firstActivity && today.items.length === 0 ? <Card style={{ gap: spacing.sm }}>
        <AppText weight="800" size={16}>{isFa ? firstActivity.name_fa : firstActivity.name_en}</AppText>
        <Button full={false} label={firstActivity.activity_type === "lesson" ? (isFa ? "شروع اولین درس" : "Start first lesson") : (isFa ? "شروع اولین آزمون" : "Start first quiz")}
          onPress={() => firstActivity.activity_type === "lesson" ? navigate("lessonList", { code: firstActivity.atc_code, studyPlan: true })
            : navigate("quiz", { planChapter: firstActivity.atc_code, planTitle: isFa ? firstActivity.name_fa : firstActivity.name_en })} />
      </Card> : null}
      <Card style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: spacing.sm }}>
          <AppText accessibilityRole="header" weight="900" size={18}>{isFa ? "برنامهٔ امروز" : "Today’s study plan"}</AppText>
          <Button label={t("planningEditPlan")} full={false} variant="secondary" onPress={() => navigate("planningSetup")} style={{ minHeight: 44 }} />
        </View>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <AppText muted weight="700" size={12}>{n(doneCount)}/{n(today.items.length)} {isFa ? "انجام شده" : "completed"}</AppText>
          <AppText muted weight="700" size={12}>{n(today.total_minutes)} {t("planningTodayMinutes")}</AppText>
        </View>
        <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, now: pct, max: 100 }}
          style={{ height: 6, borderRadius: 3, backgroundColor: colors.trackBg, flexDirection: row, overflow: "hidden" }}>
          <View style={{ width: `${pct}%`, height: 6, backgroundColor: colors.accent }} />
        </View>
      </Card>
      {complete.isError || skip.isError ? <AppText accessibilityRole="alert" color={colors.denyLabel}>{t("planningSaveError")}</AppText> : null}
      {pending.map((item, index) => (
        <PlanItemRow key={item.id} item={item} label={t(index === 0 ? "planningNowLabel" : "planningNextLabel")}
          busy={complete.isPending || skip.isPending} onOpen={() => openActivity(item)}
          onComplete={() => complete.mutate(item.id)} onSkip={() => skip.mutate(item.id)} />
      ))}
      {pending.length === 0 ? <Card><AppText size={14} weight="800">{today.items.length ? t("planningAllDoneTitle")
        : isFa ? "امروز فعالیت زمان‌بندی‌شده‌ای ندارید." : "No activities are scheduled for today."}</AppText></Card> : null}
      {learningPath}
      {today.week.length > 0 ? (
        <Card style={{ gap: spacing.sm }}>
          <AppText accessibilityRole="header" weight="800" size={15}>{isFa ? "این هفته" : "This week"}</AppText>
          <View style={{ flexDirection: row, gap: 4 }}>
            {today.week.map((day, i) => {
              const label = DAY_LABELS_SHORT[lang][i];
              const current = day.state === "today";
              const done = day.state === "done";
              const caption = current ? (isFa ? "امروز" : "Today") : done ? (isFa ? "انجام شد" : "Done") : day.study_day ? (isFa ? "روز مطالعه" : "Study day") : (isFa ? "استراحت" : "Rest day");
              return (
                <View accessible accessibilityLabel={`${label} · ${caption}`} key={day.date}
                  style={{ flex: 1, minHeight: 48, justifyContent: "center", borderRadius: 9, backgroundColor: current ? colors.accent : colors.softBg }}>
                  <AppText center size={11} weight="700" color={current ? colors.onAccent : colors.ink}>{label}</AppText>
                  <AppText center size={11} color={current ? colors.onAccent : colors.accent}>{done ? "✓" : day.study_day ? "•" : "–"}</AppText>
                </View>
              );
            })}
          </View>
        </Card>
      ) : null}

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
                {isFa ? item.title_fa : item.title_en}
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
  busy,
}: {
  item: StudyPlanItem;
  label: string;
  onOpen: () => void;
  onComplete: () => void;
  onSkip: () => void;
  busy: boolean;
}) {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();

  return (
    <Card style={{ padding: 13, gap: 10 }}>
      <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
        <AppText weight="800" size={11} color={colors.accent}>
          {label}
        </AppText>
        <AppText muted weight="700" size={11}>
          {n(item.estimated_minutes)} {isFa ? "دقیقه" : "min"}
        </AppText>
      </View>
      <AppText weight="800" size={14}>
        {isFa ? item.title_fa : item.title_en}
      </AppText>
      {item.reason_fa || item.reason_en ? (
        <AppText muted weight="600" size={12} style={{ lineHeight: 18 }}>
          {isFa ? item.reason_fa : item.reason_en}
        </AppText>
      ) : null}
      <View style={{ flexDirection: row, gap: 8, marginTop: 2, flexWrap: "wrap" }}>
        <Pressable
          accessibilityRole="button"
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
          accessibilityRole="button"
          disabled={busy}
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
          accessibilityRole="button"
          disabled={busy}
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
    </Card>
  );
}
