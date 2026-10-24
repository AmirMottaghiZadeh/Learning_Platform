import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo, useState } from "react";
import { Pressable, View } from "react-native";

import { lessonsApi, meApi } from "@/api/endpoints";
import { PlanMode } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_FULL, StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { groupByCategory } from "@/utils/lessonCategories";

const MODES: { key: PlanMode; titleKey: StringKey; descKey: StringKey }[] = [
  { key: "none", titleKey: "planningModeNoneTitle", descKey: "planningModeNoneDesc" },
  { key: "goal", titleKey: "planningModeGoalTitle", descKey: "planningModeGoalDesc" },
  { key: "maintenance", titleKey: "planningModeMaintenanceTitle", descKey: "planningModeMaintenanceDesc" },
];

const DAY_MS = 24 * 60 * 60 * 1000;

/** Mode + topics + deadline + daily time + study days, all one form: the
 * three planning models share enough fields (topics, daily minutes, days,
 * reminders) that splitting them into separate screens would just duplicate
 * this layout three times. */
export function PlanningSetupScreen() {
  const { t, isFa, lang, row } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const qc = useQueryClient();

  const { data: plan, isLoading: planLoading } = useQuery({ queryKey: ["plan"], queryFn: meApi.plan });
  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });
  const categories = useMemo(() => groupByCategory(groups ?? []), [groups]);

  const [mode, setMode] = useState<PlanMode>("none");
  const [topicKeys, setTopicKeys] = useState<string[]>([]);
  const [dailyMinutes, setDailyMinutes] = useState("30");
  const [deadlineDays, setDeadlineDays] = useState("14");
  const [days, setDays] = useState<boolean[]>([false, false, false, false, false, false, false]);
  const [reminders, setReminders] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fitsWarning, setFitsWarning] = useState(false);

  useEffect(() => {
    if (!plan) return;
    setMode(plan.mode);
    setTopicKeys(plan.topic_keys);
    setDailyMinutes(String(plan.daily_minutes));
    setDays(plan.days);
    setReminders(plan.reminders_enabled);
    if (plan.deadline) {
      const diff = Math.round((new Date(plan.deadline).getTime() - Date.now()) / DAY_MS);
      setDeadlineDays(String(Math.max(1, diff)));
    }
  }, [plan]);

  const toggleTopic = (key: string) =>
    setTopicKeys((cur) => (cur.includes(key) ? cur.filter((k) => k !== key) : [...cur, key]));

  const save = useMutation({
    mutationFn: () => {
      const minutes = Math.max(5, Math.min(240, parseInt(dailyMinutes, 10) || 30));
      const deadline =
        mode === "goal"
          ? new Date(Date.now() + Math.max(1, parseInt(deadlineDays, 10) || 1) * DAY_MS)
              .toISOString()
              .slice(0, 10)
          : null;
      return meApi.savePlan({
        mode,
        topic_keys: mode === "none" ? [] : topicKeys,
        daily_minutes: minutes,
        deadline,
        days,
        reminders_enabled: reminders,
      });
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["plan"] });
      qc.invalidateQueries({ queryKey: ["plan-today"] });
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
    save.mutate();
  };

  if (planLoading) return <LoadingState />;

  const labels = DAY_LABELS_FULL[lang];

  return (
    <Screen>
      <ScreenChrome title={t("planningSetupTitle")} onBack={goBack} />

      <View style={{ gap: 10, marginBottom: spacing.lg }}>
        {MODES.map((m) => {
          const active = mode === m.key;
          return (
            <Pressable
              key={m.key}
              onPress={() => setMode(m.key)}
              style={[
                {
                  borderRadius: 16,
                  borderWidth: 1.5,
                  borderColor: active ? colors.accent : colors.border,
                  backgroundColor: active ? `${colors.accent}14` : colors.cardBg,
                  padding: 14,
                },
                shadows.raisedSm,
              ]}
            >
              <AppText weight="800" size={14} color={active ? colors.accent : colors.ink}>
                {t(m.titleKey)}
              </AppText>
              <AppText muted weight="600" size={12} style={{ marginTop: 4 }}>
                {t(m.descKey)}
              </AppText>
            </Pressable>
          );
        })}
      </View>

      {mode !== "none" ? (
        <>
          <AppText weight="800" size={14} style={{ marginBottom: 6 }}>
            {t("planningPickTopicsLabel")}
          </AppText>
          {mode === "maintenance" ? (
            <AppText muted weight="600" size={12} style={{ marginBottom: 10 }}>
              {t("planningPickTopicsOptionalHint")}
            </AppText>
          ) : null}

          {groupsLoading ? (
            <LoadingState />
          ) : (
            <View style={{ gap: 14, marginBottom: spacing.lg }}>
              {categories.map((category) => (
                <View key={category.code}>
                  <AppText weight="800" size={12} muted style={{ marginBottom: 6 }}>
                    {isFa ? category.name_fa : category.name_en}
                  </AppText>
                  <View style={{ gap: 6 }}>
                    {category.topics.map((topic) => {
                      const checked = topicKeys.includes(topic.code);
                      const total = topic.subgroups.reduce((a, s) => a + s.total, 0);
                      const done = topic.subgroups.reduce((a, s) => a + s.done, 0);
                      return (
                        <Pressable
                          key={topic.code}
                          onPress={() => toggleTopic(topic.code)}
                          style={{
                            flexDirection: row,
                            alignItems: "center",
                            gap: 10,
                            paddingVertical: 9,
                            paddingHorizontal: 12,
                            borderRadius: 12,
                            backgroundColor: checked ? `${colors.accent}14` : colors.softBg,
                            borderWidth: 1,
                            borderColor: checked ? colors.accent : colors.trackBg,
                          }}
                        >
                          <View
                            style={{
                              width: 18,
                              height: 18,
                              borderRadius: 5,
                              backgroundColor: checked ? colors.accent : "transparent",
                              borderWidth: checked ? 0 : 1.5,
                              borderColor: colors.trackBg,
                            }}
                          />
                          <AppText
                            weight="700"
                            size={13}
                            style={{ flex: 1 }}
                            color={checked ? colors.accent : colors.ink}
                          >
                            {isFa ? topic.name_fa : topic.name_en}
                          </AppText>
                          <AppText muted size={11} weight="700">
                            {done}/{total}
                          </AppText>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>
              ))}
            </View>
          )}

          <AppText weight="800" size={14} style={{ marginBottom: 6 }}>
            {t("planningDailyMinutesLabel")}
          </AppText>
          <Input
            keyboardType="number-pad"
            value={dailyMinutes}
            onChangeText={setDailyMinutes}
            style={{ marginBottom: spacing.lg }}
          />

          {mode === "goal" ? (
            <>
              <AppText weight="800" size={14} style={{ marginBottom: 6 }}>
                {t("planningDeadlineDaysLabel")}
              </AppText>
              <Input
                keyboardType="number-pad"
                value={deadlineDays}
                onChangeText={setDeadlineDays}
                style={{ marginBottom: spacing.lg }}
              />
            </>
          ) : null}
        </>
      ) : null}

      <AppText weight="800" size={14} style={{ marginBottom: 10 }}>
        {t("planningDaysLabel")}
      </AppText>
      <View style={{ gap: 8, marginBottom: spacing.lg }}>
        {labels.map((label, i) => {
          const on = days[i];
          return (
            <Pressable
              key={i}
              onPress={() => setDays((d) => d.map((v, j) => (j === i ? !v : v)))}
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 12,
                height: 50,
                paddingHorizontal: 16,
                borderRadius: 14,
                backgroundColor: on ? `${colors.accent}1a` : colors.softBg,
                borderWidth: 1.5,
                borderColor: on ? colors.accent : colors.trackBg,
              }}
            >
              <View
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  backgroundColor: on ? colors.accent : "transparent",
                  borderWidth: on ? 0 : 1.5,
                  borderColor: colors.trackBg,
                }}
              />
              <AppText weight="700" size={14} color={on ? colors.accent : colors.ink}>
                {label}
              </AppText>
            </Pressable>
          );
        })}
      </View>

      <Pressable
        onPress={() => setReminders((v) => !v)}
        style={{
          flexDirection: row,
          alignItems: "center",
          justifyContent: "space-between",
          height: 48,
          paddingHorizontal: 16,
          borderRadius: 14,
          backgroundColor: colors.softBg,
          marginBottom: spacing.lg,
        }}
      >
        <AppText weight="700" size={14}>
          {t("profileNotifications")}
        </AppText>
        <View
          style={{
            width: 44,
            height: 26,
            borderRadius: 13,
            backgroundColor: reminders ? colors.accent : colors.trackBg,
            padding: 3,
            alignItems: reminders ? "flex-end" : "flex-start",
          }}
        >
          <View style={{ width: 20, height: 20, borderRadius: 10, backgroundColor: "#fff" }} />
        </View>
      </Pressable>

      {error ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginBottom: 12 }}>
          {error}
        </AppText>
      ) : null}
      {fitsWarning ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginBottom: 12 }}>
          {t("planningFitsWarning")}
        </AppText>
      ) : null}

      <Button label={t("planningSave")} onPress={handleSave} loading={save.isPending} />
    </Screen>
  );
}
