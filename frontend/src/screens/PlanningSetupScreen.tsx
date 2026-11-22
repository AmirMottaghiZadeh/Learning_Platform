import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo, useState } from "react";
import { Pressable, View } from "react-native";

import { lessonsApi, meApi } from "@/api/endpoints";
import { PlanMode } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { ExamDatePicker } from "@/components/plan/PlanPickers";
import { PLAN_BRIEF_KEY } from "@/components/plan/PlanSection";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Chevron } from "@/components/primitives/Chevron";
import { Input } from "@/components/primitives/Input";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_FULL, DAY_LABELS_SHORT, StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { groupByCategory } from "@/utils/lessonCategories";
import { daysUntil } from "@/utils/planDates";

const MODES: { key: PlanMode; titleKey: StringKey; descKey: StringKey }[] = [
  { key: "none", titleKey: "planningModeNoneTitle", descKey: "planningModeNoneDesc" },
  { key: "goal", titleKey: "planningModeGoalTitle", descKey: "planningModeGoalDesc" },
  { key: "maintenance", titleKey: "planningModeMaintenanceTitle", descKey: "planningModeMaintenanceDesc" },
];

/** Settings for the student schedule, shared by the two scheduled modes. */
export function PlanningSetupScreen() {
  const { t, isFa, lang, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const qc = useQueryClient();

  const planQuery = useQuery({ queryKey: ["plan"], queryFn: meApi.plan, retry: false });
  const plan = planQuery.data;
  const groupsQuery = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });
  const categories = useMemo(() => groupByCategory(groupsQuery.data ?? []), [groupsQuery.data]);

  const [mode, setMode] = useState<PlanMode>("none");
  const [topicKeys, setTopicKeys] = useState<string[]>([]);
  const [dailyMinutes, setDailyMinutes] = useState("30");
  const [deadline, setDeadline] = useState<string | null>(null);
  const [days, setDays] = useState<boolean[]>([false, false, false, false, false, false, false]);
  const [topicQuery, setTopicQuery] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fitsWarning, setFitsWarning] = useState(false);

  useEffect(() => {
    if (!plan) return;
    setMode(plan.mode);
    setTopicKeys(plan.topic_keys);
    setDailyMinutes(String(plan.daily_minutes));
    setDays(plan.days);
    // A deadline already past is no exam date to keep.
    setDeadline(plan.deadline && daysUntil(plan.deadline) > 0 ? plan.deadline : null);
  }, [plan]);

  const toggleTopic = (key: string) =>
    setTopicKeys((cur) => (cur.includes(key) ? cur.filter((k) => k !== key) : [...cur, key]));

  const save = useMutation({
    mutationFn: () => {
      const minutes = Math.max(5, Math.min(240, parseInt(dailyMinutes.replace(/[۰-۹]/g, (digit) => String(digit.charCodeAt(0) - 0x06f0)), 10) || 30));
      return meApi.savePlan({
        mode,
        topic_keys: mode === "none" ? [] : topicKeys,
        daily_minutes: minutes,
        deadline: mode === "goal" ? deadline : null,
        days,
        reminders_enabled: false,
      });
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["plan"] });
      qc.invalidateQueries({ queryKey: ["plan-today"] });
      qc.invalidateQueries({ queryKey: PLAN_BRIEF_KEY });
      if (result.fits_deadline === false) {
        setFitsWarning(true);
        return;
      }
      goBack();
    },
    onError: () => setError(t("planningSaveError")),
  });

  const handleSave = () => {
    setError(null);
    setFitsWarning(false);
    if (mode === "goal" && topicKeys.length === 0) {
      setError(t("planningNoTopicsSelected"));
      return;
    }
    if (mode !== "none" && !days.some(Boolean)) {
      setError(isFa ? "دست‌کم یک روز برای مطالعه انتخاب کنید." : "Select at least one study day.");
      return;
    }
    if (mode === "goal" && !deadline) {
      setError(t("planningNoDeadline"));
      return;
    }
    save.mutate();
  };

  const term = topicQuery.trim().toLocaleLowerCase();
  const visibleCategories = categories.map((category) => ({
    ...category,
    topics: category.topics.filter((topic) => `${category.name_fa} ${category.name_en} ${topic.name_fa} ${topic.name_en}`.toLocaleLowerCase().includes(term)),
  })).filter((category) => category.topics.length > 0);
  const modeHeading = isFa ? "نوع برنامه" : "Schedule type";

  return (
    <Screen contentStyle={{ maxWidth: 790, gap: spacing.md }} keyboardShouldPersistTaps="handled">
      <ScreenChrome title={t("planningSetupTitle")} onBack={goBack} />

      {planQuery.isPending ? <LoadingState /> : planQuery.isError ? (
        <Card>
          <AppText muted accessibilityRole="alert">{t("loadFailed")}</AppText>
          <Button label={t("retry")} full={false} variant="secondary" onPress={() => void planQuery.refetch()} />
        </Card>
      ) : (
        <>
          <Card style={{ gap: spacing.sm }}>
            <AppText accessibilityRole="header" weight="800" size={16}>{modeHeading}</AppText>
            <View accessibilityRole="radiogroup" style={{ gap: spacing.xs }}>
              {MODES.map((option) => {
                const active = mode === option.key;
                return (
                  <Pressable key={option.key} accessibilityRole="radio" accessibilityState={{ checked: active }}
                    onPress={() => setMode(option.key)}
                    style={{ borderRadius: 13, backgroundColor: active ? colors.leitnerActiveBg : colors.softBg, padding: 12 }}>
                    <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
                      <AppText weight="800" size={14} color={active ? colors.accent : colors.ink} style={{ flex: 1 }}>{t(option.titleKey)}</AppText>
                      {active ? <AppText color={colors.accent} aria-hidden>✓</AppText> : null}
                    </View>
                    <AppText muted size={12}>{t(option.descKey)}</AppText>
                  </Pressable>
                );
              })}
            </View>
          </Card>

          {mode !== "none" ? (
            <>
              <Card style={{ gap: spacing.sm }}>
                <AppText accessibilityRole="header" weight="800" size={16}>{isFa ? "زمان مطالعه" : "Study time"}</AppText>
                <AppText weight="700" size={13}>{t("planningDailyMinutesLabel")}</AppText>
                <Input keyboardType="number-pad" maxLength={3} accessibilityLabel={t("planningDailyMinutesLabel")}
                  value={dailyMinutes} onChangeText={setDailyMinutes} />
                <AppText weight="700" size={13}>{t("planningDaysLabel")}</AppText>
                <View style={{ flexDirection: row, gap: spacing.xs, flexWrap: "wrap" }}>
                  {DAY_LABELS_FULL[lang].map((label, i) => {
                    const on = days[i];
                    return (
                      <Pressable key={label} accessibilityRole="button" accessibilityState={{ selected: on }} accessibilityLabel={label}
                        onPress={() => setDays((current) => current.map((value, j) => (i === j ? !value : value)))}
                        style={{ minHeight: 44, minWidth: 42, paddingHorizontal: 8, justifyContent: "center", borderRadius: 10,
                          backgroundColor: on ? colors.accent : colors.softBg }}>
                        <AppText center size={12} weight="800" color={on ? colors.onAccent : colors.ink}>{DAY_LABELS_SHORT[lang][i]}</AppText>
                      </Pressable>
                    );
                  })}
                </View>
                {mode === "goal" ? (
                  <View style={{ gap: spacing.xs }}>
                    <AppText weight="700" size={13}>{t("planningDeadlineLabel")}</AppText>
                    <ExamDatePicker key={plan?.deadline ?? "none"} value={deadline} onChange={setDeadline} />
                  </View>
                ) : null}
              </Card>

              <Card style={{ gap: spacing.sm }}>
                <View style={{ flexDirection: row, alignItems: "baseline", justifyContent: "space-between", gap: spacing.sm }}>
                  <AppText accessibilityRole="header" weight="800" size={16} style={{ flex: 1 }}>{t("planningPickTopicsLabel")}</AppText>
                  <AppText muted size={12}>{isFa ? `${n(topicKeys.length)} انتخاب` : `${n(topicKeys.length)} selected`}</AppText>
                </View>
                {mode === "maintenance" ? <AppText muted size={12}>{t("planningPickTopicsOptionalHint")}</AppText> : null}
                {groupsQuery.isPending ? <LoadingState /> : groupsQuery.isError ? (
                  <Button full={false} label={t("retry")} variant="secondary" onPress={() => void groupsQuery.refetch()} />
                ) : (
                  <>
                    <Input value={topicQuery} onChangeText={setTopicQuery}
                      placeholder={isFa ? "جست‌وجوی موضوع درسی" : "Find a study topic"}
                      accessibilityLabel={isFa ? "جست‌وجوی موضوع درسی" : "Find a study topic"} />
                    {visibleCategories.length === 0 ? <AppText muted size={13}>{isFa ? "موضوعی پیدا نشد." : "No study topics found."}</AppText> : null}
                    {visibleCategories.map((category) => {
                      const open = Boolean(term) || expanded === category.code;
                      const selected = category.topics.filter((topic) => topicKeys.includes(topic.code)).length;
                      return (
                        <View key={category.code} style={{ gap: 4 }}>
                          <Pressable onPress={() => setExpanded((current) => current === category.code ? null : category.code)}
                            accessibilityRole="button" accessibilityState={{ expanded: open }} disabled={Boolean(term)}
                            style={{ flexDirection: row, alignItems: "center", gap: spacing.xs, minHeight: 46, borderRadius: 10,
                              backgroundColor: colors.softBg, paddingHorizontal: 10 }}>
                            <AppText weight="700" size={13} style={{ flex: 1 }}>{isFa ? category.name_fa : category.name_en}</AppText>
                            {selected ? <AppText size={12} color={colors.accent}>{n(selected)}</AppText> : null}
                            {!term ? <View style={{ transform: [{ rotate: open ? "90deg" : "0deg" }] }}><Chevron /></View> : null}
                          </Pressable>
                          {open ? category.topics.map((topic) => {
                            const checked = topicKeys.includes(topic.code);
                            return (
                              <Pressable key={topic.code} accessibilityRole="checkbox" accessibilityState={{ checked }} onPress={() => toggleTopic(topic.code)}
                                style={{ flexDirection: row, alignItems: "center", gap: spacing.sm, minHeight: 44, borderRadius: 9, paddingHorizontal: 10,
                                  backgroundColor: checked ? colors.leitnerActiveBg : "transparent" }}>
                                <AppText size={13} weight={checked ? "800" : "600"} style={{ flex: 1 }}>{isFa ? topic.name_fa : topic.name_en}</AppText>
                                {checked ? <AppText color={colors.accent} aria-hidden>✓</AppText> : null}
                              </Pressable>
                            );
                          }) : null}
                        </View>
                      );
                    })}
                  </>
                )}
              </Card>
            </>
          ) : null}

          {error || fitsWarning ? (
            <AppText accessibilityRole="alert" size={13} weight="700" color={colors.denyLabel}>{error || t("planningFitsWarning")}</AppText>
          ) : null}
          <Button label={t("planningSave")} onPress={handleSave} loading={save.isPending} />
        </>
      )}
    </Screen>
  );
}
