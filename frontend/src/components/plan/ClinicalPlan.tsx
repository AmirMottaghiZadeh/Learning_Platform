import AsyncStorage from "@react-native-async-storage/async-storage";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { IconImage, IconName } from "@/components/primitives/IconImage";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { isoDay } from "@/utils/planDates";

export type StudyTrack = "student" | "clinical";

const SOURCES = [
  { key: "uptodate", icon: "uptodate-logo", fa: "آپتودیت", en: "UpToDate", hintFa: "مقاله‌ای دربارهٔ یک موضوع بالینی", hintEn: "Read about a clinical topic",
    suggestions: ["Asthma", "Atrial fibrillation", "Type 2 diabetes"] },
  { key: "lexicomp", icon: "lexicomp-logo", fa: "لکسی‌کامپ", en: "LexiComp", hintFa: "مرور تداخل داروهای انتخابی", hintEn: "Review interactions between selected drugs",
    suggestions: ["warfarin", "metformin", "amiodarone"] },
  { key: "diseasesConditions", icon: "entry-diseases", fa: "بیماری‌های مداسکیپ", en: "Medscape diseases", hintFa: "مرور یک بیماری یا وضعیت بالینی", hintEn: "Review a disease or condition",
    suggestions: ["Pneumonia", "Migraine", "Heart failure"] },
  { key: "guidelines", icon: "entry-guidelines", fa: "گایدلاین‌های مداسکیپ", en: "Medscape guidelines", hintFa: "گایدلاین مرتبط با یک موضوع بالینی", hintEn: "Find guidelines on a clinical topic",
    suggestions: ["Hypertension", "Asthma", "Diabetes"] },
] as const satisfies ReadonlyArray<{ key: string; icon: IconName; fa: string; en: string; hintFa: string; hintEn: string; suggestions: readonly string[] }>;

type Source = typeof SOURCES[number];
type SourceKey = Source["key"];
type ClinicalTask = { topic: string; secondDrug?: string; completedOn?: string };
type ClinicalTasks = Partial<Record<SourceKey, ClinicalTask>>;
type StoredPlan = { track: StudyTrack; tasks: ClinicalTasks };

export function useStudyTrack() {
  const user = useAuth((s) => s.user);
  const key = `pharmenta.study-track.${user?.id}`;
  const fallback: StudyTrack = user?.profile.study_goal === "clinical" ? "clinical" : "student";
  const query = useQuery({
    queryKey: ["study-workflow", key],
    queryFn: async (): Promise<StoredPlan> => {
      const saved = await AsyncStorage.getItem(key);
      if (!saved) return { track: fallback, tasks: {} };
      const plan = JSON.parse(saved) as StoredPlan;
      return { track: plan.track === "clinical" ? "clinical" : "student", tasks: plan.tasks ?? {} };
    },
  });
  const client = useQueryClient();
  const save = useMutation({
    scope: { id: key },
    mutationFn: async (update: (prev: StoredPlan) => StoredPlan) => {
      const raw = await AsyncStorage.getItem(key);
      const next = update(raw ? JSON.parse(raw) as StoredPlan : { track: fallback, tasks: {} });
      await AsyncStorage.setItem(key, JSON.stringify(next));
      return next;
    },
    onSuccess: (next) => client.setQueryData(["study-workflow", key], next),
  });
  return { query, save, track: query.data?.track ?? fallback, tasks: query.data?.tasks ?? {} };
}

export function ClinicalPlan({ state }: { state: ReturnType<typeof useStudyTrack> }) {
  const { isFa, n } = useLang();
  const day = isoDay(new Date());
  const remaining = SOURCES.filter(({ key }) => state.tasks[key]?.topic && state.tasks[key]?.completedOn !== day);
  const completed = SOURCES.filter(({ key }) => state.tasks[key]?.completedOn === day).length;
  const configured = SOURCES.filter(({ key }) => state.tasks[key]?.topic).length;
  const updateTask = (key: SourceKey, task?: ClinicalTask) => state.save.mutateAsync((previous) => ({
    ...previous, tasks: { ...previous.tasks, [key]: task },
  }));
  return (
    <View style={{ gap: spacing.md }} testID="clinical-study-plan">
      <Card style={{ gap: spacing.xs }}>
        <AppText size={20} weight="900" accessibilityRole="header">{isFa ? "مرور بالینی امروز" : "Today’s clinical reading"}</AppText>
        <AppText muted size={13}>{configured
          ? (isFa ? `${n(completed)} از ${n(configured)} فعالیت انجام شده` : `${completed} of ${configured} activities completed`)
          : (isFa ? "برای هر منبع یک موضوع دلخواه بنویسید یا از موضوع‌های پیشنهادی انتخاب کنید." : "Enter a topic for each source or choose from the suggestions.")}</AppText>
      </Card>
      {SOURCES.map((source) => (
        <SourceTask key={source.key} source={source} task={state.tasks[source.key]}
          day={day} next={source.key === remaining[0]?.key} busy={state.save.isPending}
          onChange={(task) => updateTask(source.key, task)} />
      ))}
    </View>
  );
}

function SourceTask({ source, task, day, next, busy, onChange }: {
  source: Source; task?: ClinicalTask; day: string; next: boolean; busy: boolean; onChange: (task?: ClinicalTask) => Promise<StoredPlan>;
}) {
  const { isFa, row, t } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);
  const [draft, setDraft] = useState<string | null>(null);
  const [second, setSecond] = useState("");
  const editing = draft !== null || !task?.topic;
  const done = task?.completedOn === day;
  const title = isFa ? source.fa : source.en;
  const hint = isFa ? source.hintFa : source.hintEn;
  const drugPair = source.key === "lexicomp";
  const firstLabel = drugPair ? (isFa ? "داروی اول" : "First drug") : hint;
  const secondLabel = isFa ? "داروی دوم (اختیاری)" : "Second drug (optional)";
  return (
    <Card testID={`clinical-plan-${source.key}`} style={{ gap: spacing.sm }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
        <IconImage name={source.icon} size={29} />
        <View style={{ flex: 1 }}>
          <AppText size={15} weight="800">{title}</AppText>
          <AppText size={12} muted>{hint}</AppText>
        </View>
        {next || done ? <AppText color={colors.accent} size={12} weight="700">
          {done ? (isFa ? "انجام شد" : "Done") : (isFa ? "کار بعدی" : "Up next")}
        </AppText> : null}
      </View>
      {editing ? (
        <>
          <Input placeholder={firstLabel} accessibilityLabel={`${title} · ${firstLabel}`} value={draft ?? ""} onChangeText={setDraft}
            maxLength={120} autoCapitalize="none" />
          {drugPair ? <Input placeholder={secondLabel} accessibilityLabel={secondLabel} value={second} onChangeText={setSecond}
            maxLength={120} autoCapitalize="none" /> : null}
          <View style={{ flexDirection: row, flexWrap: "wrap", gap: 5 }}>
            {source.suggestions.map((suggestion) => (
              <Pressable key={suggestion} accessibilityRole="button" onPress={() => setDraft(suggestion)}
                style={{ minHeight: 44, justifyContent: "center", paddingHorizontal: 9, borderRadius: 10, backgroundColor: colors.softBg }}>
                <AppText size={12}>{suggestion}</AppText>
              </Pressable>
            ))}
          </View>
          <View style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.xs }}>
            <Button full={false} label={isFa ? "ذخیرهٔ موضوع" : "Save topic"} disabled={!draft?.trim() || busy}
              onPress={() => {
                const topic = draft?.trim();
                if (!topic) return;
                const secondDrug = drugPair ? second.trim() || undefined : undefined;
                const same = topic === task?.topic && secondDrug === task?.secondDrug;
                void onChange({ topic, secondDrug, completedOn: same ? task?.completedOn : undefined })
                  .then(() => { setDraft(null); setSecond(""); }, () => undefined);
              }} />
            {task?.topic ? <>
              <Button full={false} variant="ghost" label={isFa ? "انصراف" : "Cancel"} onPress={() => { setDraft(null); setSecond(""); }} />
              <Button full={false} variant="ghost" disabled={busy} label={isFa ? "حذف موضوع" : "Remove topic"}
                onPress={() => void onChange().then(() => { setDraft(null); setSecond(""); }, () => undefined)} />
            </> : null}
          </View>
        </>
      ) : (
        <>
          <AppText size={14} weight="700" selectable>{[task?.topic, task?.secondDrug].filter(Boolean).join(" + ")}</AppText>
          <View style={{ flexDirection: row, gap: spacing.xs, flexWrap: "wrap" }}>
            <Button full={false} label={isFa ? "باز کردن منبع" : "Open reference"}
              onPress={() => navigate(source.key, { query: task?.topic ?? "", ...(task?.secondDrug ? { nextQuery: task.secondDrug } : {}) })} />
            <Button full={false} variant="secondary" disabled={busy}
              label={done ? (isFa ? "بازگردانی" : "Undo") : t("planningMarkDone")}
              onPress={() => { if (task) void onChange({ ...task, completedOn: done ? undefined : day }).catch(() => undefined); }} />
            <Button full={false} variant="ghost" label={isFa ? "ویرایش موضوع" : "Edit topic"}
              onPress={() => { setDraft(task?.topic ?? ""); setSecond(task?.secondDrug ?? ""); }} />
          </View>
        </>
      )}
    </Card>
  );
}

export function StudyTrackSelector({ state }: { state: ReturnType<typeof useStudyTrack> }) {
  const { isFa, row, t } = useLang();
  const { colors } = useTheme();
  if (state.query.isPending) return <LoadingState />;
  if (state.query.isError) return <Card><AppText>{t("loadFailed")}</AppText><Button variant="ghost" label={t("retry")} onPress={() => void state.query.refetch()} /></Card>;
  const labels = { student: isFa ? "دانشجوی داروسازی" : "Pharmacy student", clinical: isFa ? "شاغل در بالین" : "Clinical practice" };
  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: row, gap: spacing.sm }} accessibilityRole="radiogroup">
        {(["student", "clinical"] as const).map((track) => {
          const active = state.track === track;
          return (
            <Pressable key={track} accessibilityRole="radio" accessibilityState={{ checked: active, disabled: state.save.isPending }}
              disabled={state.save.isPending}
              onPress={() => { if (!active) state.save.mutate((current) => ({ ...current, track })); }}
              style={{ flex: 1, minHeight: 52, borderRadius: 14, justifyContent: "center", padding: 8, backgroundColor: active ? colors.accent : colors.softBg }}>
              <AppText center weight="800" size={13} color={active ? colors.onAccent : colors.ink}>{labels[track]}</AppText>
            </Pressable>
          );
        })}
      </View>
      {state.save.isError ? <AppText accessibilityRole="alert" color={colors.denyLabel}>{t("planningSaveError")}</AppText> : null}
    </View>
  );
}
