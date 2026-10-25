import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { ApiError } from "@/api/client";
import { meApi } from "@/api/endpoints";
import { PlanDay, PlanToday, StudyPlanItem } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_SHORT } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { isoDay } from "@/utils/planDates";

export const PLAN_BRIEF_KEY = ["plan-today-brief"];

function Check({ color, size }: { color: string; size: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3}>
      <Path d="M5 12l5 5 9-10" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

const fill = (template: string, values: Record<string, string>) =>
  template.replace(/\{(\w+)\}/g, (_, k) => values[k] ?? "");

/** The home screen's study plan, under the entry tiles: one line on where
 * the plan stands (days to the exam, which week), today's tasks and this
 * week. The plan itself comes from the onboarding answers or the plan
 * editor (backend progress.planning). A learner whose plan doesn't include
 * study planning sees `fallback` -- the plain next-chapter card. */
export function PlanSection({ fallback }: { fallback: React.ReactNode }) {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);

  // Refetched every time home shows: a lesson read or a quiz finished
  // elsewhere ticks its task off on the server.
  const { data, isLoading, error } = useQuery({
    queryKey: PLAN_BRIEF_KEY,
    queryFn: meApi.planTodayBrief,
    staleTime: 0,
    refetchOnMount: "always",
  });

  const head = (
    <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
      <AppText weight="800" size={13}>
        {t("planSectionTitle")}
      </AppText>
      <Pressable onPress={() => navigate("planningSetup")} hitSlop={8} accessibilityRole="button">
        <AppText weight="800" size={12} color={colors.accent}>
          {t("editPlan")}
        </AppText>
      </Pressable>
    </View>
  );

  // No planning in the learner's plan, or no answer at all (offline with
  // nothing cached): the plain next-chapter card instead.
  if ((error instanceof ApiError && error.code === "PREMIUM_REQUIRED") || (error && !data)) return <>{fallback}</>;
  if (isLoading || !data) return null;
  if (data.mode === "none") {
    return (
      <View>
        {head}
        <Card style={{ alignItems: "center", paddingVertical: 24, gap: 8 }}>
          <AppText weight="800" size={15} center>
            {t("planningEmptyTitle")}
          </AppText>
          <AppText muted weight="600" size={12.5} center style={{ lineHeight: 21, maxWidth: 300 }}>
            {t("planningEmptyBody")}
          </AppText>
          <Button
            label={t("planningCreateCta")}
            full={false}
            onPress={() => navigate("planningSetup")}
            style={{ marginTop: 6, alignSelf: "center" }}
          />
        </Card>
      </View>
    );
  }
  return (
    <View>
      {head}
      <SummaryLine data={data} />
      <TodayBox data={data} />
      <WeekBox data={data} />
    </View>
  );
}

function SummaryLine({ data }: { data: PlanToday }) {
  const { t, n, isFa, row } = useLang();
  const { colors } = useTheme();
  const s = data.summary;
  if (data.mode === "maintenance") {
    return (
      <AppText weight="700" size={12.5} muted style={{ marginBottom: 10 }}>
        {fill(t("planMaintenanceLine"), { m: n(s.daily_minutes) })}
      </AppText>
    );
  }
  if (s.days_left == null) return null;
  const parts = [
    s.days_left === 0 ? t("planExamToday") : fill(t("planDaysLeft"), { n: n(s.days_left) }),
    s.week_index != null && s.week_count != null ? fill(t("planWeekOf"), { i: n(s.week_index), c: n(s.week_count) }) : "",
  ].filter(Boolean);
  const pct = s.progress_pct ?? 0;
  return (
    <View style={{ marginBottom: 10, gap: 6 }}>
      <View style={{ flexDirection: row, justifyContent: "space-between" }}>
        <AppText weight="700" size={12.5} muted>
          {parts.join(t("listSeparator"))}
        </AppText>
        <AppText weight="800" size={12.5} color={colors.accent}>
          {isFa ? `${n(pct)}٪` : `${pct}%`}
        </AppText>
      </View>
      <View style={{ height: 5, borderRadius: 3, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row }}>
        <View style={{ width: `${Math.min(100, pct)}%`, height: "100%", borderRadius: 3, backgroundColor: colors.accent }} />
      </View>
    </View>
  );
}

function useOpenActivity() {
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);
  return (item: StudyPlanItem) => {
    if (item.activity_type === "lesson" && item.atc_code) navigate("lessonList", { code: item.atc_code });
    else if (item.activity_type === "mistake_review") navigate("mistakes");
    else if (item.activity_type === "quiz") setTab("quiz");
    else if (item.activity_type === "flashcards") setTab("flashcards");
  };
}

function TodayBox({ data }: { data: PlanToday }) {
  const { t, n, isFa, row } = useLang();
  const { colors } = useTheme();
  const qc = useQueryClient();
  const open = useOpenActivity();
  const complete = useMutation({
    mutationFn: (id: number) => meApi.completePlanItem(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PLAN_BRIEF_KEY });
      qc.invalidateQueries({ queryKey: ["plan-today"] });
    },
  });

  const items = data.items;
  const next = items.find((i) => i.status === "pending");
  const today = data.week.find((d) => d.date === isoDay(new Date()));
  const title = (i: StudyPlanItem) => (isFa ? i.title_fa : i.title_en);

  let empty: string | null = null;
  if (!items.length) empty = today && !today.study_day ? t("planFreeDay") : t("planNothingLeft");
  else if (!next) empty = t("planAllDone");

  return (
    <Card style={{ marginBottom: spacing.md }}>
      <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "baseline" }}>
        <AppText weight="900" size={15}>
          {t("planToday")}
        </AppText>
        {items.length ? (
          <AppText weight="700" size={12} muted>
            {fill(t("planMinutes"), { m: n(data.total_minutes) })}
          </AppText>
        ) : null}
      </View>

      {items.length ? (
        <View style={{ marginTop: 10 }}>
          {items.map((item, i) => {
            const done = item.status !== "pending";
            const isNext = item.id === next?.id;
            return (
              <View
                key={item.id}
                style={{
                  flexDirection: row,
                  alignItems: "center",
                  gap: 12,
                  paddingVertical: 10,
                  borderBottomWidth: i < items.length - 1 ? 1 : 0,
                  borderBottomColor: colors.sheetLine,
                }}
              >
                <Pressable
                  onPress={done ? undefined : () => complete.mutate(item.id)}
                  disabled={done}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: done }}
                  accessibilityLabel={title(item)}
                  hitSlop={9}
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 13,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: done ? colors.accent : "transparent",
                    borderWidth: done ? 0 : 2,
                    borderColor: isNext ? colors.accent : colors.trackBg,
                  }}
                >
                  {done ? <Check color={colors.onAccent} size={14} /> : null}
                </Pressable>
                <Pressable onPress={() => open(item)} style={{ flex: 1, gap: 2 }} accessibilityRole="button">
                  <AppText
                    weight="800"
                    size={13.5}
                    color={done ? colors.muted : colors.ink}
                    style={done ? { textDecorationLine: "line-through" } : undefined}
                  >
                    {title(item)}
                  </AppText>
                  <AppText weight="600" size={11.5} muted>
                    {done
                      ? `${fill(t("planMinutes"), { m: n(item.estimated_minutes) })}${t("listSeparator")}${t("planningMarkDone")}`
                      : fill(t("planMinutes"), { m: n(item.estimated_minutes) })}
                  </AppText>
                </Pressable>
                {isNext ? (
                  <View style={{ paddingHorizontal: 9, paddingVertical: 4, borderRadius: 999, backgroundColor: colors.leitnerActiveBg }}>
                    <AppText weight="800" size={11} color={colors.accent}>
                      {t("planningNextLabel")}
                    </AppText>
                  </View>
                ) : null}
              </View>
            );
          })}
        </View>
      ) : null}

      {empty ? (
        <AppText weight="600" size={13} muted style={{ marginTop: items.length ? 10 : 8 }}>
          {empty}
        </AppText>
      ) : null}
      {next ? (
        <Button label={`${t("planningStartActivity")}: ${title(next)}`} onPress={() => open(next)} style={{ marginTop: 12, height: 46 }} />
      ) : null}
    </Card>
  );
}

function DayCell({ day, label }: { day: PlanDay; label: string }) {
  const { t } = useLang();
  const { colors } = useTheme();
  const box = { width: 32, height: 32, borderRadius: 10, alignItems: "center" as const, justifyContent: "center" as const };
  let cell: React.ReactNode;
  switch (day.state) {
    case "done":
      cell = (
        <View style={[box, { backgroundColor: colors.accent }]}>
          <Check color={colors.onAccent} size={13} />
        </View>
      );
      break;
    case "today":
      cell = (
        <View style={[box, { borderWidth: 2, borderColor: colors.accent }]}>
          <AppText weight="800" size={9.5} color={colors.accent}>
            {t("planDayToday")}
          </AppText>
        </View>
      );
      break;
    case "missed":
      cell = (
        <View style={[box, { backgroundColor: colors.denyBg, borderWidth: 1, borderColor: colors.denyBorder }]}>
          <View style={{ width: 10, height: 2, borderRadius: 1, backgroundColor: colors.denyLabel }} />
        </View>
      );
      break;
    case "planned":
      cell = <View style={[box, { backgroundColor: colors.softBg, borderWidth: 1, borderColor: colors.trackBg }]} />;
      break;
    default:
      cell = (
        <View style={box}>
          <AppText weight="700" size={10} muted>
            {day.state === "free" ? t("planDayFree") : "–"}
          </AppText>
        </View>
      );
  }
  const stateLabel: Record<PlanDay["state"], string> = {
    done: t("planningMarkDone"),
    today: t("planDayToday"),
    missed: t("planDayMissed"),
    planned: t("planDayPlanned"),
    free: t("planDayFree"),
    off: "",
  };
  return (
    <View style={{ flex: 1, alignItems: "center", gap: 6 }} accessible accessibilityLabel={`${label}: ${stateLabel[day.state]}`}>
      <AppText weight={day.state === "today" ? "800" : "700"} size={11} color={day.state === "today" ? colors.accent : colors.muted}>
        {label}
      </AppText>
      {cell}
    </View>
  );
}

function WeekBox({ data }: { data: PlanToday }) {
  const { t, n, lang, row } = useLang();
  if (!data.week.length) return null;
  const study = data.week.filter((d) => d.study_day && d.state !== "off");
  const done = study.filter((d) => d.state === "done").length;
  const labels = DAY_LABELS_SHORT[lang];
  return (
    <Card>
      <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "baseline" }}>
        <AppText weight="900" size={14}>
          {t("planWeek")}
        </AppText>
        <AppText weight="700" size={11.5} muted>
          {fill(t("planWeekCount"), { d: n(done), t: n(study.length) })}
        </AppText>
      </View>
      <View style={{ flexDirection: row, marginTop: 12 }}>
        {data.week.map((day, i) => (
          <DayCell key={day.date} day={day} label={labels[i]} />
        ))}
      </View>
      {data.mode === "goal" ? (
        <AppText weight="600" size={12} muted style={{ marginTop: 12, lineHeight: 20 }}>
          {t("planRescheduleNote")}
        </AppText>
      ) : null}
    </Card>
  );
}
