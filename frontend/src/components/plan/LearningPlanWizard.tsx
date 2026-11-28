import { useMutation, useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { meApi } from "@/api/endpoints";
import type { AtcPlanActivity, AtcPlanConfig } from "@/api/types";
import { ExamDatePicker, MinutesPicker, StudyDaysPicker } from "@/components/plan/PlanPickers";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { TextInput } from "@/components/primitives/TextInput";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing } from "@/theme/tokens";
import { daysUntil, formatDay } from "@/utils/planDates";

export const DEFAULT_PLAN: AtcPlanConfig = {
  atc_groups: [], daily_minutes: 30, days: [true, false, true, false, true, false, false], deadline: null,
};

type Props = {
  initial?: AtcPlanConfig;
  bottomInset?: number;
  isEditing?: boolean;
  onClose: () => void | Promise<void>;
  onSave: (config: AtcPlanConfig, first: AtcPlanActivity | null) => Promise<void>;
};

const normalize = (text: string) => text.toLowerCase().replace(/ي/g, "ی").replace(/ك/g, "ک").replace(/[\s‌]+/g, "");

export function LearningPlanWizard({ initial = DEFAULT_PLAN, bottomInset = 0, isEditing, onClose, onSave }: Props) {
  const { isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const [step, setStep] = useState(0);
  const [config, setConfig] = useState(initial);
  const [hasDate, setHasDate] = useState(!!initial.deadline);
  const [search, setSearch] = useState("");
  const groupsQuery = useQuery({ queryKey: ["plan-atc-groups"], queryFn: meApi.planGroups, staleTime: Infinity, retry: false });
  const groups = groupsQuery.data ?? [];
  const preview = useMutation({ mutationFn: meApi.previewPlan });
  const finalize = useMutation({
    mutationFn: (skip: boolean) => skip ? Promise.resolve(onClose())
      : onSave(config, preview.data?.first_lesson ?? preview.data?.first_activity ?? null),
  });
  const loading = preview.isPending || finalize.isPending;
  const l = (fa: string, en: string) => isFa ? fa : en;
  const groupName = (code: string) => {
    const group = groups.find((item) => item.code === code);
    return group ? l(group.name_fa, group.name_en) : code;
  };
  const back = () => {
    if (finalize.isPending) return;
    if (step > 0) {
      setStep(step - 1);
      finalize.reset();
    } else if (isEditing) onClose();
  };
  useBackInterceptor(step > 0 || finalize.isPending, back);

  const showPreview = (value: AtcPlanConfig) => {
    setStep(2);
    preview.mutate(value);
  };
  const move = (index: number, delta: number) => {
    const order = [...config.atc_groups];
    const destination = index + delta;
    [order[index], order[destination]] = [order[destination], order[index]];
    const next = { ...config, atc_groups: order };
    setConfig(next);
    showPreview(next);
  };
  const current = preview.data;
  const term = normalize(search);
  const visible = groups.filter((group) => [group.code, group.name_fa, group.name_en].some((value) => normalize(value).includes(term)));
  const titles = [
    l("چه دسته‌هایی را می‌خواهید بخوانید؟", "What would you like to study?"),
    l("چه روزهایی و چقدر وقت دارید؟", "When and how long can you study?"),
    l("برنامهٔ پیشنهادی شما", "Your proposed study plan"),
  ];
  const daySummary = l(`${n(config.daily_minutes)} دقیقه در روز · ${n(config.days.filter(Boolean).length)} روز در هفته`,
    `${config.daily_minutes} min per day · ${config.days.filter(Boolean).length} days per week`);
  const allowContinue = step === 0 ? groupsQuery.isSuccess && config.atc_groups.length > 0
    : step === 1 ? config.days.some(Boolean) && (!hasDate || !!config.deadline && daysUntil(config.deadline) > 0)
    : !!current?.fits_deadline && current.chapter_count > 0;
  const skipLabel = isEditing ? l("بستن", "Close") : l("ورود به خانه", "Go to home");

  const field = (label: string, control: React.ReactNode) => (
    <View style={{ gap: spacing.sm }}>
      <AppText weight="800" size={15}>{label}</AppText>
      {control}
    </View>
  );

  return (
    <View style={{ direction: "ltr", flex: 1, width: "100%", maxWidth: 700, alignSelf: "center", backgroundColor: colors.appBg }}>
      <View style={{ minHeight: 62, backgroundColor: colors.headerMesh, flexDirection: row, alignItems: "center",
        justifyContent: "space-between", gap: spacing.sm, paddingHorizontal: spacing.lg }}>
        <AppText size={15} weight="800" color={colors.flipFrontInk}>{l("فارمنتا", "Pharmenta")}</AppText>
        <AppText size={12} color={colors.flipFrontSub}>{l(`مرحلهٔ ${n(step + 1)} از ۳`, `Step ${step + 1} of 3`)}</AppText>
        <Pressable accessibilityRole="button" accessibilityState={{ disabled: finalize.isPending }}
          onPress={() => finalize.mutate(true)} disabled={finalize.isPending}
          style={{ minHeight: 44, justifyContent: "center" }}>
          <AppText size={12} color={colors.flipFrontInk}>{skipLabel}</AppText>
        </Pressable>
      </View>
      <ScrollView key={step} style={{ flex: 1 }} keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ padding: spacing.lg, gap: spacing.md }}>
        <AppText accessibilityRole="header" aria-level={1} size={25} weight="900">{titles[step]}</AppText>
        {step === 0 ? <>
          <AppText size={13} muted>{l("دست‌کم یک گروه از ۱۴ دستهٔ اصلی ATC انتخاب کنید. ترتیب انتخاب، اولویت مطالعه است.",
            "Select at least one of the 14 main ATC groups. Selection order sets your study priority.")}</AppText>
          {groupsQuery.isPending ? <LoadingState /> : groupsQuery.isError
            ? <Button label={l("دریافت دسته‌ها · تلاش دوباره", "Could not load groups. Retry")} onPress={() => void groupsQuery.refetch()} />
            : <>
              <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
                <TextInput value={search} onChangeText={setSearch}
                  accessibilityLabel={l("جست‌وجوی دسته‌ها", "Find groups")} placeholder={l("نام گروه یا کد ATC", "Group name or ATC code")}
                  placeholderTextColor={colors.muted} style={{ flex: 1, minWidth: 0, minHeight: 44, borderRadius: radius.input,
                    backgroundColor: colors.cardBg, color: colors.ink, paddingHorizontal: spacing.md, textAlign: isFa ? "right" : "left" }} />
                <Button full={false} variant="ghost" style={{ paddingHorizontal: spacing.xs }}
                  label={config.atc_groups.length === groups.length ? l("پاک‌کردن انتخاب", "Clear selection") : l("انتخاب همه", "Select all")}
                  onPress={() => setConfig({ ...config, atc_groups: config.atc_groups.length === groups.length ? []
                    : [...config.atc_groups, ...groups.filter((group) => !config.atc_groups.includes(group.code)).map((group) => group.code)] })} />
              </View>
              <View style={{ flexDirection: row, flexWrap: "wrap", justifyContent: "space-between", gap: spacing.sm }}>
                {visible.map((group) => {
                  const selected = config.atc_groups.includes(group.code);
                  return <Pressable key={group.code} testID={`plan-atc-${group.code}`} accessibilityRole="checkbox"
                    accessibilityLabel={groupName(group.code)} accessibilityState={{ checked: selected }} aria-checked={selected}
                    onPress={() => setConfig({ ...config, atc_groups: selected ? config.atc_groups.filter((code) => code !== group.code)
                      : [...config.atc_groups, group.code] })}
                    style={({ pressed }) => [{ width: "48%", minHeight: 56, borderRadius: radius.input, padding: spacing.sm,
                      flexDirection: row, alignItems: "center", gap: spacing.xs,
                      // Keep the surface opaque: Android draws elevation as a grey
                      // ring around a translucent background, which made a selected
                      // box look thickly bordered. The tint is painted on top instead.
                      backgroundColor: colors.cardBg, opacity: pressed ? 0.75 : 1 }, shadows.raisedSm]}>
                      {selected ? <View pointerEvents="none"
                        style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0,
                          borderRadius: radius.input, backgroundColor: colors.leitnerActiveBg }} /> : null}
                      <AppText size={12} weight={selected ? "800" : "600"} style={{ flex: 1 }}>{groupName(group.code)}</AppText>
                      <AppText size={11} weight="800" color={colors.accent} style={{ writingDirection: "ltr" }}>
                        {selected ? `✓ ${group.code}` : group.code}
                      </AppText>
                  </Pressable>;
                })}
                {!visible.length ? <AppText muted size={13}>{l("دسته‌ای پیدا نشد.", "No matching groups.")}</AppText> : null}
              </View>
            </>}
        </> : step === 1 ? <>
          {field(l("زمان روزانه", "Daily study time"), <MinutesPicker value={config.daily_minutes}
            options={[...new Set([15, 30, 45, 60, 90, config.daily_minutes])].sort((a, b) => a - b)}
            onChange={(daily_minutes) => setConfig({ ...config, daily_minutes })} />)}
          {field(l("روزهای مطالعه", "Study days"), <StudyDaysPicker value={config.days} onChange={(days) => setConfig({ ...config, days })} />)}
          {field(l("تاریخ آزمون", "Exam date"), <>
            <View style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
              <Button variant={hasDate ? "secondary" : "primary"} full={false} label={l("فعلاً تاریخ ندارم", "No date yet")}
                onPress={() => { setHasDate(false); setConfig({ ...config, deadline: null }); }} />
              <Button variant={hasDate ? "primary" : "secondary"} full={false} label={l("تاریخ دارم", "I have a date")}
                onPress={() => setHasDate(true)} />
            </View>
            {hasDate ? <ExamDatePicker value={config.deadline} onChange={(deadline) => setConfig({ ...config, deadline })} /> : null}
          </>)}
        </> : <>
          <Card raised style={{ gap: spacing.sm }}>
            <AppText size={15} weight="800">{l("دسته‌ها به ترتیب مطالعه", "Groups in study order")}</AppText>
            {config.atc_groups.map((code, index) => <View key={code} style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
              <AppText size={13} style={{ flex: 1 }}>{n(index + 1)}. {groupName(code)}</AppText>
              {([-1, 1] as const).map((delta) => {
                const disabled = loading || index + delta < 0 || index + delta >= config.atc_groups.length;
                return <Pressable key={delta} accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled}
                  accessibilityLabel={`${delta < 0 ? l("بالا بردن", "Move up") : l("پایین بردن", "Move down")} ${groupName(code)}`}
                  onPress={() => move(index, delta)} style={{ width: 44, height: 44, borderRadius: radius.input,
                    alignItems: "center", justifyContent: "center", backgroundColor: colors.softBg, opacity: disabled ? 0.45 : 1 }}>
                    <AppText color={colors.accent}>{delta < 0 ? "↑" : "↓"}</AppText>
                  </Pressable>;
              })}
            </View>)}
            <Button full={false} variant="ghost" label={l("ویرایش دسته‌ها", "Edit groups")} disabled={finalize.isPending} onPress={() => setStep(0)} />
          </Card>
          <Card raised style={{ gap: spacing.xs }}>
            <AppText size={15} weight="800">{daySummary}</AppText>
            <AppText size={13} muted>{config.deadline ? formatDay(config.deadline, isFa, n) : l("بدون تاریخ آزمون", "No exam date")}</AppText>
            <Button full={false} variant="ghost" label={l("ویرایش زمان مطالعه", "Edit study time")} disabled={finalize.isPending} onPress={() => setStep(1)} />
          </Card>
          {preview.isPending ? <LoadingState /> : preview.isError
            ? <Button variant="secondary" label={l("دریافت پیش‌نمایش · تلاش دوباره", "Could not preview. Retry")} onPress={() => showPreview(config)} />
            : current ? <>
              <Card raised style={{ gap: spacing.xs }}>
                {current.first_activity ? <AppText weight="800">{l("اولین فعالیت", "First activity")} ·
                  {" "}{current.first_activity.activity_type === "lesson" ? l("دارونامه", "Drugbank") : l("آزمون", "Quiz")}
                  {" · "}{l(current.first_activity.name_fa, current.first_activity.name_en)}</AppText>
                  : current.chapter_count > 0 ? <AppText size={13}>{l("برای این گروه‌ها کار تازه‌ای باقی نمانده است.", "There is no remaining work for these groups.")}</AppText> : null}
                <AppText muted size={13}>{l(`${n(current.remaining_minutes)} دقیقه مطالعه · ${n(current.study_sessions)} جلسه در پیش‌نمایش`,
                  `${current.remaining_minutes} study minutes · ${current.study_sessions} previewed sessions`)}</AppText>
                {current.estimated_finish ? <AppText muted size={13}>{l("پایان تقریبی", "Estimated finish")} · {formatDay(current.estimated_finish, isFa, n)}</AppText> : null}
                <AppText muted size={12}>{l("دارونامه، سپس آزمون همان فصل · فلش‌کارت به‌زودی", "Drugbank, then its chapter quiz · Flashcards coming soon")}</AppText>
              </Card>
              {!current.fits_deadline ? <AppText accessibilityRole="alert" size={13} color={colors.denyLabel}>
                {l("زمان تا آزمون کافی نیست. تاریخ، زمان مطالعه یا تعداد دسته‌ها را تغییر دهید.", "The plan does not fit before the exam. Adjust the date, study time, or groups.")}
              </AppText> : null}
              {current.empty_groups.length ? <AppText size={13} muted>{l("فصل در دسترس نیست برای", "No chapters available for")} · {current.empty_groups.map(groupName).join(l("، ", ", "))}</AppText> : null}
              {current.missing_quiz_count ? <AppText size={13} muted>{l(`${n(current.missing_quiz_count)} فصل فعلاً سؤال کافی ندارد.`,
                `${current.missing_quiz_count} chapters do not currently have enough quiz questions.`)}</AppText> : null}
            </> : null}
        </>}
        {finalize.isError ? <AppText accessibilityRole="alert" size={13} color={colors.denyLabel}>
          {l("ذخیره انجام نشد. انتخاب‌ها محفوظ‌اند. دوباره تلاش کنید.", "Saving failed. Your choices are still here. Try again.")}
        </AppText> : null}
      </ScrollView>
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.sm, paddingBottom: bottomInset + spacing.md,
        flexDirection: row, gap: spacing.sm, justifyContent: "space-between", alignItems: "center", backgroundColor: colors.cardBg }}>
        {step > 0 ? <Button full={false} variant="ghost" label={l("بازگشت", "Back")} disabled={finalize.isPending} onPress={back} />
          : <AppText size={12} muted accessibilityLiveRegion="polite">{l(`${n(config.atc_groups.length)} دسته انتخاب شده`, `${config.atc_groups.length} selected`)}</AppText>}
        <Button full={false} disabled={!allowContinue || loading} loading={finalize.isPending}
          label={step === 0 ? l("ادامه", "Continue") : step === 1 ? l("دیدن برنامه", "Preview plan") : l("ساخت برنامه", "Save plan")}
          onPress={() => {
            finalize.reset();
            if (step === 0) setStep(1);
            else if (step === 1) showPreview(config);
            else finalize.mutate(false);
          }} />
      </View>
    </View>
  );
}
