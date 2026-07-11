import React, {useMemo, useState} from "react";
import {Pressable, StyleSheet, Text, TextInput, View} from "react-native";
import {BookOpenCheck, CalendarDays, CheckCircle2, Clock3, ListChecks, Target} from "lucide-react-native";

import {LearningCard, PrimaryButton, ProgressBar, ScreenContainer, ScreenHeader, SecondaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";

const subjects = ["نام تجاری", "با غذا / بی غذا", "اندیکاسیون", "عوارض"];

export function PlanningScreen({onNavigate}: {onNavigate: (screen: ScreenKey) => void}) {
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState("مرور هدفمند داروها برای آزمون");
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>(subjects.slice(0, 2));
  const [deadline, setDeadline] = useState("30");
  const [dailyMinutes, setDailyMinutes] = useState("35");
  const progress = ((step + 1) / 5) * 100;
  const dailyCards = useMemo(() => Math.max(8, Math.round(Number(dailyMinutes || 0) / 3)), [dailyMinutes]);

  function toggleSubject(subject: string) {
    setSelectedSubjects((items) =>
      items.includes(subject) ? items.filter((item) => item !== subject) : [...items, subject],
    );
  }

  return (
    <ScreenContainer>
      <ScreenHeader eyebrow="Adaptive planning" title="Study plan" />
      <LearningCard tone="mint">
        <View style={styles.stepTop}>
          <View style={styles.stepIcon}>
            <CalendarDays size={22} color={colors.primary} />
          </View>
          <View style={styles.stepCopy}>
            <Text style={styles.stepLabel}>Step {step + 1} of 5</Text>
            <Text style={styles.stepTitle}>Build a focused daily route</Text>
          </View>
        </View>
        <ProgressBar value={progress} />
      </LearningCard>

      {step === 0 ? (
        <LearningCard tone="blue">
          <Target size={24} color={colors.primary} />
          <Text style={styles.title}>هدفت چیست؟</Text>
          <Text style={styles.text}>هدف باید کوتاه و قابل اقدام باشد تا داشبورد امروز بتواند قدم بعدی را پیشنهاد کند.</Text>
          <TextInput value={goal} onChangeText={setGoal} style={styles.input} placeholder="مثلاً آماده‌سازی آزمون ماه آینده" placeholderTextColor={colors.softText} />
        </LearningCard>
      ) : null}

      {step === 1 ? (
        <LearningCard tone="lavender">
          <BookOpenCheck size={24} color={colors.primary} />
          <Text style={styles.title}>چه درس‌هایی داری؟</Text>
          <Text style={styles.text}>به‌جای فرم طولانی، فقط مسیرهای مهم را انتخاب کن.</Text>
          <View style={styles.chips}>
            {subjects.map((subject) => {
              const selected = selectedSubjects.includes(subject);
              return (
                <Pressable
                  key={subject}
                  accessibilityRole="button"
                  onPress={() => toggleSubject(subject)}
                  style={[styles.chip, selected && styles.chipActive]}
                >
                  <Text style={[styles.chipText, selected && styles.chipTextActive]}>{subject}</Text>
                </Pressable>
              );
            })}
          </View>
        </LearningCard>
      ) : null}

      {step === 2 ? (
        <LearningCard tone="amber">
          <CalendarDays size={24} color={colors.primary} />
          <Text style={styles.title}>تا کی وقت داری؟</Text>
          <Text style={styles.text}>فعلاً این برنامه در فرانت‌اند پیش‌نمایش می‌شود و قوانین زمان‌بندی اصلی همچنان سمت بک‌اند می‌ماند.</Text>
          <TextInput keyboardType="numeric" value={deadline} onChangeText={setDeadline} style={styles.input} placeholder="روز باقی‌مانده" placeholderTextColor={colors.softText} />
        </LearningCard>
      ) : null}

      {step === 3 ? (
        <LearningCard tone="rose">
          <Clock3 size={24} color={colors.primary} />
          <Text style={styles.title}>روزی چقدر زمان می‌گذاری؟</Text>
          <Text style={styles.text}>زمان روزانه به تخمین کارت و آزمون تبدیل می‌شود؛ تصمیم آموزشی نهایی هنوز از API می‌آید.</Text>
          <TextInput keyboardType="numeric" value={dailyMinutes} onChangeText={setDailyMinutes} style={styles.input} placeholder="دقیقه در روز" placeholderTextColor={colors.softText} />
        </LearningCard>
      ) : null}

      {step === 4 ? (
        <LearningCard tone="sage">
          <ListChecks size={24} color={colors.primary} />
          <Text style={styles.title}>خلاصه مسیر</Text>
          <Text style={styles.summary}>Goal: {goal}</Text>
          <Text style={styles.summary}>Subjects: {selectedSubjects.join(" · ") || "No subjects selected"}</Text>
          <Text style={styles.summary}>{deadline || 0} days · {dailyMinutes || 0} minutes/day · about {dailyCards} cards/day</Text>
          <PrimaryButton label="Start from today" Icon={CheckCircle2} onPress={() => onNavigate("dashboard")} />
        </LearningCard>
      ) : null}

      <View style={styles.actions}>
        <SecondaryButton label="Back" onPress={() => setStep((value) => Math.max(0, value - 1))} disabled={step === 0} />
        <PrimaryButton label={step === 4 ? "Open dashboard" : "Continue"} onPress={() => (step === 4 ? onNavigate("dashboard") : setStep((value) => value + 1))} />
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  stepTop: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  stepIcon: {
    width: 48,
    height: 48,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  stepCopy: {
    flex: 1,
  },
  stepLabel: {
    color: colors.primary,
    fontWeight: "900",
  },
  stepTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginTop: spacing.xs,
  },
  title: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  text: {
    color: colors.muted,
    fontWeight: "800",
    lineHeight: 22,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  input: {
    minHeight: 52,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    color: colors.ink,
    fontWeight: "800",
    paddingHorizontal: spacing.md,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  chip: {
    minHeight: 42,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  chipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  chipText: {
    color: colors.muted,
    fontWeight: "900",
  },
  chipTextActive: {
    color: colors.black,
  },
  summary: {
    color: colors.ink,
    fontWeight: "800",
    lineHeight: 24,
    marginBottom: spacing.md,
  },
  actions: {
    gap: spacing.sm,
  },
});
