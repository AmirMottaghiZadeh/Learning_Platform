import React, {useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {ArrowLeft, Brain, CalendarCheck, CheckCircle2, Layers, RotateCcw, Sparkles, Target} from "lucide-react-native";
import type {LucideIcon} from "lucide-react-native";

import {InstallPrompt} from "../components/InstallPrompt";
import {TypewriterText} from "../components/TypewriterText";
import {LearningCard, PrimaryButton, ProgressBar, SecondaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";

const steps: Array<{
  title: string;
  body: string;
  takeaway: string;
  Icon: LucideIcon;
  tone: "mint" | "blue" | "amber" | "rose" | "lavender";
}> = [
  {
    title: "هر روز دقیقاً بدان از کجا شروع کنی",
    body: "K_Game به‌جای لیست‌کردن محتوا، برنامه امروز را از وضعیت واقعی یادگیری تو می‌سازد.",
    takeaway: "هدف صفحه خانه: پاسخ به سؤال «الان چه کار کنم؟»",
    Icon: Target,
    tone: "mint",
  },
  {
    title: "یادگیری فقط تست‌زدن نیست",
    body: "چرخه محصول از یادگیری، آزمون، بازخورد، مرور اشتباهات و فلش‌کارت تشکیل می‌شود.",
    takeaway: "یک حلقه کامل، دلیل برگشتن فردا را می‌سازد.",
    Icon: Brain,
    tone: "blue",
  },
  {
    title: "مرور باید به‌موقع و قابل لمس باشد",
    body: "فلش‌کارت‌ها و Leitner Box کمک می‌کنند کارت‌های جدید، مرور و بازیادگیری از هم جدا دیده شوند.",
    takeaway: "کارت‌های due مهم‌ترین اقدام بعدی تو هستند.",
    Icon: Layers,
    tone: "amber",
  },
  {
    title: "نقاط ضعف باید روشن باشند",
    body: "اشتباهات و موضوعات ضعیف جدا نمایش داده می‌شوند تا تلاش بیشتر، هدفمندتر شود.",
    takeaway: "پیشرفت واقعی یعنی کاهش ابهام، نه فقط افزایش زمان مطالعه.",
    Icon: RotateCcw,
    tone: "rose",
  },
  {
    title: "مسیرت را بساز و شروع کن",
    body: "بعد از ورود، داشبورد امروز، آزمون سریع، مرور کارت‌ها و آمار مسیر را در دسترس داری.",
    takeaway: "یک CTA اصلی، یک قدم بعدی، بدون سردرگمی.",
    Icon: CalendarCheck,
    tone: "lavender",
  },
];

export function OnboardingScreen({onDone}: {onDone: () => void}) {
  const [index, setIndex] = useState(0);
  const [instantText, setInstantText] = useState(false);
  const step = steps[index];
  const progress = ((index + 1) / steps.length) * 100;
  const isLast = index === steps.length - 1;

  function next() {
    setInstantText(false);
    if (isLast) {
      onDone();
      return;
    }
    setIndex((value) => value + 1);
  }

  function back() {
    setInstantText(false);
    setIndex((value) => Math.max(0, value - 1));
  }

  return (
    <View style={styles.root}>
      <View style={styles.phoneFrame}>
        <InstallPrompt />
        <View style={styles.progressTop}>
          <Pressable accessibilityRole="button" disabled={index === 0} onPress={back} style={styles.backButton}>
            <ArrowLeft size={20} color={index === 0 ? colors.softText : colors.primary} />
          </Pressable>
          <View style={styles.progressWrap}>
            <ProgressBar value={progress} />
          </View>
          <Text style={styles.stepCounter}>{index + 1}/{steps.length}</Text>
        </View>

        <LearningCard tone={step.tone} style={styles.storyCard}>
          <View style={styles.visual}>
            <View style={styles.orbit}>
              <step.Icon size={42} color={colors.primaryStrong} />
            </View>
            <View style={[styles.dot, styles.dotOne]} />
            <View style={[styles.dot, styles.dotTwo]} />
          </View>
          <TypewriterText text={step.title} style={styles.title} instant={instantText} />
          <TypewriterText text={step.body} style={styles.body} delay={180} speed={10} instant={instantText} />
          <View style={styles.takeaway}>
            <Sparkles size={18} color={colors.primary} />
            <TypewriterText text={step.takeaway} style={styles.takeawayText} delay={520} speed={8} instant={instantText} />
          </View>
        </LearningCard>

        <View style={styles.actions}>
          <SecondaryButton label="نمایش سریع" onPress={() => setInstantText(true)} />
          <PrimaryButton label={isLast ? "شروع یادگیری" : "ادامه"} Icon={isLast ? CheckCircle2 : undefined} onPress={next} />
          <Pressable accessibilityRole="button" onPress={onDone} style={styles.skipButton}>
            <Text style={styles.skipText}>بعداً می‌بینم</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.md,
  },
  phoneFrame: {
    width: "100%",
    maxWidth: 430,
    flex: 1,
    justifyContent: "center",
  },
  progressTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  progressWrap: {
    flex: 1,
  },
  stepCounter: {
    color: colors.muted,
    fontWeight: "900",
  },
  storyCard: {
    minHeight: 470,
    justifyContent: "space-between",
  },
  visual: {
    minHeight: 180,
    borderRadius: radius.xl,
    backgroundColor: "rgba(255,255,255,0.58)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.xl,
    overflow: "hidden",
  },
  orbit: {
    width: 112,
    height: 112,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  dot: {
    position: "absolute",
    width: 58,
    height: 58,
    borderRadius: radius.pill,
    backgroundColor: "rgba(31,143,139,0.14)",
  },
  dotOne: {
    top: 24,
    right: 42,
  },
  dotTwo: {
    bottom: 28,
    left: 34,
  },
  title: {
    minHeight: 78,
    color: colors.ink,
    fontSize: 26,
    fontWeight: "900",
    lineHeight: 36,
    textAlign: "right",
  },
  body: {
    minHeight: 92,
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "800",
    lineHeight: 26,
    marginTop: spacing.md,
    textAlign: "right",
  },
  takeaway: {
    minHeight: 72,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    alignItems: "center",
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  takeawayText: {
    flex: 1,
    color: colors.ink,
    fontWeight: "900",
    lineHeight: 22,
    marginLeft: spacing.sm,
    textAlign: "right",
  },
  actions: {
    gap: spacing.sm,
  },
  skipButton: {
    minHeight: 42,
    alignItems: "center",
    justifyContent: "center",
  },
  skipText: {
    color: colors.muted,
    fontWeight: "900",
  },
});
