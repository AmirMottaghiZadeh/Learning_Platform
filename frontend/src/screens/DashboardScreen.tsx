import React from "react";
import {Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import {
  AlertTriangle,
  Brain,
  CalendarCheck,
  Flame,
  Layers,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Target,
  Trophy,
} from "lucide-react-native";
import type {LucideIcon} from "lucide-react-native";
import {useQuery} from "@tanstack/react-query";

import {platformApi} from "../api/platform";
import {InstallPrompt} from "../components/InstallPrompt";
import {
  AnimatedEntrance,
  Avatar,
  BrandMark,
  ErrorState,
  LearningCard,
  MetricPill,
  PrimaryButton,
  ProgressBar,
  ProgressRing,
  ScreenContainer,
  SectionHeader,
  SkeletonCard,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";
import {useAuth} from "../store/auth";
import type {Dashboard} from "../types/api";

type QuickAction = {
  key: ScreenKey;
  label: string;
  meta: string;
  Icon: LucideIcon;
  color: string;
};

export function DashboardScreen({onNavigate}: {onNavigate: (screen: ScreenKey) => void}) {
  const {token, user} = useAuth();
  const dashboardQuery = useQuery({
    queryKey: ["dashboard", token],
    queryFn: () => platformApi.dashboard(token!),
    enabled: Boolean(token),
  });

  if (dashboardQuery.isLoading) {
    return (
      <ScreenContainer>
        <View style={styles.skeletonTopbar}>
          <SkeletonCard height={46} />
          <SkeletonCard height={46} />
        </View>
        <SkeletonCard height={118} />
        <SkeletonCard height={236} />
        <View style={styles.skeletonQuickGrid}>
          <SkeletonCard height={112} style={styles.skeletonQuickItem} />
          <SkeletonCard height={112} style={styles.skeletonQuickItem} />
          <SkeletonCard height={112} style={styles.skeletonQuickItem} />
          <SkeletonCard height={112} style={styles.skeletonQuickItem} />
        </View>
        <SkeletonCard height={170} />
        <SkeletonCard height={150} />
      </ScreenContainer>
    );
  }
  if (dashboardQuery.error) {
    return <ErrorState message={dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "بارگذاری داشبورد ممکن نیست."} onRetry={() => dashboardQuery.refetch()} />;
  }
  const dashboard = dashboardQuery.data as Dashboard | undefined;
  if (!dashboard) return null;

  const summary = dashboard.summary;
  const reviewCount = summary.due_flashcards;
  const relearnCount = summary.mistake_count;
  const learnCount = Math.max(5, 10 - Math.min(5, reviewCount));
  const totalActions = learnCount + reviewCount + relearnCount;
  const estimatedMinutes = Math.max(10, Math.round(learnCount * 1.5 + reviewCount * 2 + relearnCount * 1.2));
  const nextAction: ScreenKey = reviewCount > 0 ? "flashcards" : relearnCount > 0 ? "mistakes" : "quiz";
  const nextActionLabel = reviewCount > 0 ? "شروع مرور" : relearnCount > 0 ? "مرور اشتباهات" : "شروع آزمون";
  const quickActions: QuickAction[] = [
    {key: "quiz", label: "آزمون", meta: `${learnCount} مورد جدید`, Icon: Brain, color: colors.primary},
    {key: "flashcards", label: "فلش‌کارت", meta: `${reviewCount} مورد`, Icon: Layers, color: colors.secondary},
    {key: "mistakes", label: "اشتباهات", meta: `${relearnCount} مورد`, Icon: RotateCcw, color: colors.rose},
    {key: "league", label: "لیگ", meta: `رتبه ${dashboard.league.rank ?? "-"}`, Icon: Trophy, color: colors.amber},
  ];

  return (
    <ScreenContainer>
      <View style={styles.topbar}>
        <BrandMark />
        <View style={styles.topActions}>
          <Pressable accessibilityRole="button" onPress={() => dashboardQuery.refetch()} style={styles.iconButton}>
            <RefreshCw size={17} color={colors.muted} />
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => onNavigate("profile")}>
            <Avatar name={user?.username} />
          </Pressable>
        </View>
      </View>
      <InstallPrompt />

      <AnimatedEntrance>
        <View style={styles.greeting}>
          <Text style={styles.welcome}>خوش برگشتی، {user?.username ?? "کاربر"}!</Text>
          <Text style={styles.welcomeMeta}>آماده‌ای امروز یادگیریت را جلو ببری؟</Text>
        </View>
      </AnimatedEntrance>

      <AnimatedEntrance delay={70}>
        <LearningCard tone="primary" style={styles.hero}>
          <View pointerEvents="none" style={styles.heroGlow} />
          <View style={styles.heroContent}>
            <View style={styles.heroCopy}>
              <View style={styles.todayPill}>
                <Sparkles size={14} color={colors.primary} />
                <Text style={styles.todayPillText}>ماموریت امروز</Text>
              </View>
              <Text style={styles.heroTitle}>{nextActionLabel}</Text>
              <Text style={styles.heroMeta}>
                {estimatedMinutes} دقیقه · {totalActions} اقدام متمرکز
              </Text>
              <View style={styles.metricRow}>
                <MetricPill label="امتیاز" value={summary.xp} Icon={Target} />
                <MetricPill label="توالی" value={summary.current_streak} Icon={Flame} />
              </View>
            </View>
            <ProgressRing value={summary.accuracy_percent} label="دقت" size={112} />
          </View>
          <ProgressBar value={summary.accuracy_percent} />
          <View style={styles.heroButton}>
            <PrimaryButton label={nextActionLabel} Icon={Sparkles} onPress={() => onNavigate(nextAction)} />
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={120}>
        <View style={styles.quickGrid}>
          {quickActions.map(({key, label, meta, Icon, color}) => (
            <Pressable
              key={key}
              accessibilityRole="button"
              onPress={() => onNavigate(key)}
              style={({pressed}) => [styles.quickCard, pressed && styles.pressed]}
            >
              <View style={[styles.quickIcon, {backgroundColor: `${color}1F`}]}>
                <Icon size={21} color={color} />
              </View>
              <Text style={styles.quickTitle}>{label}</Text>
              <Text style={styles.quickMeta}>{meta}</Text>
            </Pressable>
          ))}
        </View>
      </AnimatedEntrance>

      <AnimatedEntrance delay={170}>
        <SectionHeader
          title="پیشنهاد بعدی"
          action={
            <Pressable onPress={() => onNavigate("planning")}>
              <Text style={styles.sectionAction}>ویرایش برنامه</Text>
            </Pressable>
          }
        />
        <LearningCard style={styles.eventCard}>
          <View style={styles.eventTop}>
            <View style={styles.eventIcon}>
              <CalendarCheck size={22} color={colors.black} />
            </View>
            <View style={styles.eventCopy}>
              <Text style={styles.eventEyebrow}>مسیر پیشنهادی امروز</Text>
              <Text style={styles.eventTitle}>
                {dashboard.recommendations[0]?.title ?? "روند یادگیریت را حفظ کن"}
              </Text>
              <Text style={styles.eventMeta}>
                {dashboard.recommendations[0]?.reason ?? "امروز یک جلسه متمرکز کامل کن."}
              </Text>
            </View>
          </View>
          <View style={styles.eventFooter}>
            <MetricPill label="دقیقه" value={estimatedMinutes} />
            <MetricPill label="اقدام" value={totalActions} />
            <Pressable style={styles.eventJoin} onPress={() => onNavigate(nextAction)}>
              <Text style={styles.eventJoinText}>باز کردن</Text>
            </Pressable>
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={220}>
        <SectionHeader
          title="آمار فعالیت"
          action={
            <Pressable onPress={() => onNavigate("statistics")}>
              <Text style={styles.sectionAction}>مشاهده همه</Text>
            </Pressable>
          }
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.performanceScroller}
        >
          {[
            {tone: "blue" as const, value: dashboard.activity_summary.completed_quizzes, label: "آزمون کامل‌شده"},
            {tone: "amber" as const, value: dashboard.activity_summary.answered_questions, label: "سؤال پاسخ‌داده"},
            {tone: "sage" as const, value: dashboard.activity_summary.correct_answers, label: "پاسخ صحیح"},
            {tone: "rose" as const, value: dashboard.activity_summary.wrong_answers, label: "پاسخ غلط"},
            {tone: "lavender" as const, value: dashboard.activity_summary.flashcard_reviews, label: "مرور فلش‌کارت"},
            {tone: "mint" as const, value: dashboard.activity_summary.total_study_minutes, label: "دقیقه مطالعه"},
          ].map((item) => (
            <LearningCard key={item.label} tone={item.tone} style={styles.performanceCard}>
              <Text style={styles.performanceValue}>{item.value}</Text>
              <Text style={styles.performanceLabel}>{item.label}</Text>
            </LearningCard>
          ))}
        </ScrollView>
        <LearningCard tone="mint" style={styles.reminderCard}>
          <Text style={styles.performanceValue}>{dashboard.activity_summary.pending_reminders}</Text>
          <Text style={styles.performanceLabel}>یادآوری آماده مرور</Text>
          <Text style={styles.reminderDetail}>
            {dashboard.activity_summary.saved_reminders} مورد ذخیره شده · {dashboard.activity_summary.quiz_accuracy_percent}% دقت آزمون
          </Text>
          <View style={styles.reminderAction}>
            <PrimaryButton label="مشاهده در پروفایل" onPress={() => onNavigate("profile")} />
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <SectionHeader title="نقاط ضعف" />
      {summary.weak_topics.length ? (
        summary.weak_topics.slice(0, 3).map((topic) => (
          <Pressable key={topic.topic_key} onPress={() => onNavigate("mistakes")}>
            <LearningCard tone="rose" style={styles.topicCard}>
              <View style={styles.topicIcon}>
                <AlertTriangle size={18} color={colors.rose} />
              </View>
              <View style={styles.topicCopy}>
                <Text style={styles.topicTitle}>{topic.topic_label}</Text>
                <Text style={styles.topicMeta}>{topic.wrong_answers} خطا برای مرور</Text>
              </View>
              <Text style={styles.topicScore}>{topic.accuracy_percent}%</Text>
            </LearningCard>
          </Pressable>
        ))
      ) : (
        <LearningCard tone="sage" style={styles.clearCard}>
          <Sparkles size={20} color={colors.primary} />
          <View style={styles.topicCopy}>
            <Text style={styles.topicTitle}>وضعیت خوب است</Text>
            <Text style={styles.topicMeta}>فعلاً موضوع ضعیف برجسته‌ای دیده نمی‌شود.</Text>
          </View>
        </LearningCard>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  topbar: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  skeletonTopbar: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  skeletonQuickGrid: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  skeletonQuickItem: {
    flex: 1,
  },
  topActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  greeting: {
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  welcome: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: "900",
    letterSpacing: -0.5,
  },
  welcomeMeta: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  hero: {
    overflow: "hidden",
    padding: spacing.lg,
  },
  heroGlow: {
    position: "absolute",
    width: 190,
    height: 190,
    borderRadius: radius.pill,
    backgroundColor: "rgba(32,242,138,0.11)",
    top: -90,
    right: -55,
  },
  heroContent: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  heroCopy: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  todayPill: {
    alignSelf: "flex-start",
    minHeight: 28,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    paddingHorizontal: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  todayPillText: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "900",
    marginLeft: spacing.xs,
    letterSpacing: 0.8,
  },
  heroTitle: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: "900",
    letterSpacing: -0.4,
  },
  heroMeta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  metricRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  heroButton: {
    marginTop: spacing.lg,
  },
  quickGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.sm,
  },
  quickCard: {
    width: "23%",
    minHeight: 112,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.xs,
  },
  pressed: {
    transform: [{scale: 0.97}],
    opacity: 0.9,
  },
  quickIcon: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.sm,
  },
  quickTitle: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  quickMeta: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    marginTop: 2,
  },
  sectionAction: {
    color: colors.primary,
    fontSize: typography.small,
    fontWeight: "900",
  },
  eventCard: {
    backgroundColor: colors.surfaceElevated,
    overflow: "hidden",
  },
  eventTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  eventIcon: {
    width: 50,
    height: 50,
    borderRadius: radius.lg,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  eventCopy: {
    flex: 1,
  },
  eventEyebrow: {
    color: colors.secondary,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.7,
  },
  eventTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "900",
    marginTop: spacing.xs,
  },
  eventMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  eventFooter: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  eventJoin: {
    minWidth: 72,
    minHeight: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: "auto",
  },
  eventJoinText: {
    color: colors.black,
    fontWeight: "900",
  },
  performanceScroller: {
    flexDirection: "row",
    gap: spacing.md,
    paddingBottom: spacing.xs,
  },
  performanceCard: {
    width: 150,
    minHeight: 138,
    marginBottom: 0,
  },
  reminderCard: {
    marginTop: spacing.md,
  },
  reminderAction: {
    marginTop: spacing.md,
  },
  reminderDetail: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.sm,
  },
  performanceValue: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: "900",
    marginTop: spacing.lg,
  },
  performanceLabel: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  topicCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: spacing.md,
  },
  clearCard: {
    flexDirection: "row",
    alignItems: "center",
  },
  topicIcon: {
    width: 42,
    height: 42,
    borderRadius: radius.md,
    backgroundColor: colors.roseSoft,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  topicCopy: {
    flex: 1,
    marginLeft: spacing.md,
  },
  topicTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  topicMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  topicScore: {
    color: colors.rose,
    fontSize: typography.heading,
    fontWeight: "900",
    marginLeft: spacing.md,
  },
});
