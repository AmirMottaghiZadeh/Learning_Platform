import React from "react";
import {Image, Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import type {ImageSourcePropType} from "react-native";
import {
  AlertTriangle,
  Award,
  ChevronLeft,
  Flame,
  RefreshCw,
  Sparkles,
  Target,
} from "lucide-react-native";
import {useQuery} from "@tanstack/react-query";

import {platformApi} from "../api/platform";
import {InstallPrompt} from "../components/InstallPrompt";
import {
  AnimatedEntrance,
  Avatar,
  BrandMark,
  CelebrationParticles,
  ErrorState,
  FloatingIllustration,
  GlassCard,
  LearningCard,
  MetricPill,
  PrimaryButton,
  ProgressBar,
  ScreenContainer,
  SectionHeader,
  SkeletonCard,
} from "../components/ui";
import {colors, featureAccents, radius, spacing, typography} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";
import {useAuth} from "../store/auth";
import type {Dashboard} from "../types/api";

type QuickAction = {
  key: ScreenKey;
  label: string;
  meta: string;
  source: ImageSourcePropType;
  color: string;
  soft: string;
};

type Achievement = {
  title: string;
  description: string;
  unlocked: boolean;
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
          <SkeletonCard height={58} style={styles.skeletonTopbarItem} />
        </View>
        <SkeletonCard height={118} />
        <SkeletonCard height={284} />
        <View style={styles.skeletonQuickGrid}>
          {Array.from({length: 6}, (_, index) => (
            <SkeletonCard key={index} height={124} style={styles.skeletonQuickItem} />
          ))}
        </View>
        <SkeletonCard height={152} />
      </ScreenContainer>
    );
  }
  if (dashboardQuery.error) {
    return (
      <ErrorState
        message={dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "بارگذاری داشبورد ممکن نیست."}
        onRetry={() => dashboardQuery.refetch()}
      />
    );
  }
  const dashboard = dashboardQuery.data as Dashboard | undefined;
  if (!dashboard) return null;

  const summary = dashboard.summary;
  const activity = dashboard.activity_summary;
  const reviewCount = summary.due_flashcards;
  const relearnCount = summary.mistake_count;
  const learnCount = Math.max(5, 10 - Math.min(5, reviewCount));
  const estimatedMinutes = Math.max(10, Math.round(learnCount * 1.5 + reviewCount * 2 + relearnCount * 1.2));
  const nextAction: ScreenKey = reviewCount > 0 ? "flashcards" : relearnCount > 0 ? "mistakes" : "quiz";
  const nextActionLabel = reviewCount > 0 ? "شروع مرور" : relearnCount > 0 ? "مرور اشتباهات" : "شروع آزمون";
  const journeySteps = [
    {label: "یادگیری", detail: `${learnCount} مورد`, complete: activity.answered_questions > 0},
    {label: "مرور", detail: `${reviewCount} کارت`, complete: reviewCount === 0},
    {label: "تثبیت", detail: `${relearnCount} نکته`, complete: relearnCount === 0},
  ];
  const completedJourneySteps = journeySteps.filter((item) => item.complete).length;
  const journeyProgress = (completedJourneySteps / journeySteps.length) * 100;
  const celebratesPerfectRun = summary.questions_answered > 0 && summary.accuracy_percent === 100;
  const quickActions: QuickAction[] = [
    {
      key: "quiz",
      label: "آزمون",
      meta: `${learnCount} مورد جدید`,
      source: require("../../assets/illustrations/quiz-brain.png"),
      ...featureAccents.quiz,
    },
    {
      key: "flashcards",
      label: "فلش‌کارت",
      meta: `${reviewCount} مورد`,
      source: require("../../assets/illustrations/flashcards-stack.png"),
      ...featureAccents.flashcards,
    },
    {
      key: "league",
      label: "لیگ",
      meta: `رتبه ${dashboard.league.rank ?? "-"}`,
      source: require("../../assets/illustrations/league-trophy.png"),
      ...featureAccents.leaderboard,
    },
    {
      key: "mistakes",
      label: "اشتباهات",
      meta: `${relearnCount} نکته`,
      source: require("../../assets/illustrations/mistakes-warning.png"),
      ...featureAccents.mistakes,
    },
    {
      key: "profile",
      label: "پروفایل",
      meta: `${activity.pending_reminders} یادآوری`,
      source: require("../../assets/illustrations/profile-insights.png"),
      ...featureAccents.profile,
    },
    {
      key: "statistics",
      label: "تحلیل",
      meta: `${summary.accuracy_percent}% دقت`,
      source: require("../../assets/illustrations/analytics-reports.png"),
      ...featureAccents.analytics,
    },
  ];
  const achievements: Achievement[] = [
    {
      title: "شعله‌ی مسیر",
      description: `${summary.current_streak} روز تداوم`,
      unlocked: summary.current_streak > 0,
      color: colors.amber,
    },
    {
      title: "دقت‌ساز",
      description: `${summary.accuracy_percent}% دقت ثبت‌شده`,
      unlocked: summary.questions_answered > 0 && summary.accuracy_percent >= 85,
      color: featureAccents.quiz.color,
    },
    {
      title: "پایان‌دهنده",
      description: `${activity.completed_quizzes} آزمون کامل`,
      unlocked: activity.completed_quizzes > 0,
      color: featureAccents.profile.color,
    },
  ];

  return (
    <ScreenContainer>
      <GlassCard style={styles.topbar}>
        <BrandMark />
        <View style={styles.topActions}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="به‌روزرسانی داشبورد"
            onPress={() => dashboardQuery.refetch()}
            style={({pressed}) => [styles.iconButton, pressed && styles.pressed]}
          >
            <RefreshCw size={17} color={colors.muted} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="پروفایل" onPress={() => onNavigate("profile")}>
            <Avatar name={user?.username} />
          </Pressable>
        </View>
      </GlassCard>
      <InstallPrompt />

      <AnimatedEntrance>
        <View style={styles.greeting}>
          <Text style={styles.welcome}>سلام {user?.username ?? "دوست یادگیرنده"}،</Text>
          <Text style={styles.welcomeMeta}>امروز یک قدم کوچک، مسیر تسلطت را جلو می‌برد.</Text>
        </View>
      </AnimatedEntrance>

      <AnimatedEntrance delay={70}>
        <LearningCard tone="primary" style={styles.hero}>
          <CelebrationParticles active={celebratesPerfectRun} />
          <View pointerEvents="none" style={styles.heroGlow} />
          <View style={styles.heroTop}>
            <View style={styles.heroCopy}>
              <View style={styles.todayPill}>
                <Sparkles size={14} color={colors.primary} />
                <Text style={styles.todayPillText}>سفر امروز · گام {Math.min(3, completedJourneySteps + 1)} از ۳</Text>
              </View>
              <Text style={styles.heroTitle}>{nextActionLabel}</Text>
              <Text style={styles.heroMeta}>{estimatedMinutes} دقیقه تمرکز برای ادامه‌ی مسیر کافی است.</Text>
            </View>
            <FloatingIllustration source={require("../../assets/illustrations/hero-target.png")} size={122} style={styles.heroIllustration} />
          </View>

          <View style={styles.journeyTrack}>
            {journeySteps.map((step, index) => (
              <React.Fragment key={step.label}>
                <View style={styles.journeyStep}>
                  <View style={[styles.journeyDot, step.complete && styles.journeyDotComplete]}>
                    <Text style={[styles.journeyNumber, step.complete && styles.journeyNumberComplete]}>{index + 1}</Text>
                  </View>
                  <Text style={styles.journeyLabel}>{step.label}</Text>
                  <Text style={styles.journeyDetail}>{step.detail}</Text>
                </View>
                {index < journeySteps.length - 1 ? (
                  <View style={[styles.journeyLine, step.complete && styles.journeyLineComplete]} />
                ) : null}
              </React.Fragment>
            ))}
          </View>
          <ProgressBar value={journeyProgress} />

          <View style={styles.heroFooter}>
            <View style={styles.metricRow}>
              <MetricPill label="امتیاز" value={summary.xp} Icon={Target} />
              <MetricPill label="توالی" value={summary.current_streak} Icon={Flame} />
            </View>
            <View style={styles.heroAction}>
              <PrimaryButton label={nextActionLabel} Icon={ChevronLeft} onPress={() => onNavigate(nextAction)} />
            </View>
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={120}>
        <SectionHeader title="درِ ورودی مسیرها" />
        <View style={styles.quickGrid}>
          {quickActions.map(({key, label, meta, source, color, soft}) => (
            <Pressable
              key={key}
              accessibilityRole="button"
              accessibilityLabel={label}
              onPress={() => onNavigate(key)}
              style={({pressed}) => [styles.quickCard, pressed && styles.pressed]}
            >
              <View style={[styles.quickIcon, {backgroundColor: soft, borderColor: `${color}55`}]}>
                <Image source={source} style={styles.quickIllustration} />
              </View>
              <Text style={[styles.quickTitle, {color}]}>{label}</Text>
              <Text style={styles.quickMeta}>{meta}</Text>
            </Pressable>
          ))}
        </View>
      </AnimatedEntrance>

      <AnimatedEntrance delay={170}>
        <SectionHeader title="نشان‌های مسیر" />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.achievementsScroller}>
          {achievements.map((achievement) => (
            <LearningCard
              key={achievement.title}
              style={[styles.achievementCard, !achievement.unlocked && styles.achievementLocked]}
            >
              <View style={[styles.achievementBadge, {backgroundColor: `${achievement.color}22`, borderColor: `${achievement.color}55`}]}>
                <Image source={require("../../assets/illustrations/achievement-medal.png")} style={styles.achievementImage} />
              </View>
              <View style={styles.achievementCopy}>
                <View style={styles.achievementTitleRow}>
                  <Text style={styles.achievementTitle}>{achievement.title}</Text>
                  {achievement.unlocked ? <Award size={15} color={achievement.color} /> : null}
                </View>
                <Text style={styles.achievementMeta}>
                  {achievement.unlocked ? achievement.description : "برای باز کردن، قدم بعدی را کامل کن."}
                </Text>
              </View>
            </LearningCard>
          ))}
        </ScrollView>
      </AnimatedEntrance>

      <AnimatedEntrance delay={220}>
        <SectionHeader
          title="فصل بعدی تو"
          action={
            <Pressable accessibilityRole="button" onPress={() => onNavigate("planning")}>
              <Text style={styles.sectionAction}>ویرایش برنامه</Text>
            </Pressable>
          }
        />
        <LearningCard style={styles.storyCard}>
          <View style={styles.storyIllustrationWrap}>
            <Image source={require("../../assets/illustrations/journey-road.png")} style={styles.storyIllustration} />
          </View>
          <View style={styles.storyCopy}>
            <Text style={styles.storyEyebrow}>راهنمای هوشمند</Text>
            <Text style={styles.storyTitle}>{dashboard.recommendations[0]?.title ?? "یک جلسه‌ی متمرکز بساز"}</Text>
            <Text style={styles.storyMeta}>
              {dashboard.recommendations[0]?.reason ?? "با یک تمرین کوتاه، زنجیره‌ی یادگیریت را حفظ کن."}
            </Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => onNavigate(nextAction)}
              style={({pressed}) => [styles.storyLink, pressed && styles.pressed]}
            >
              <Text style={styles.storyLinkText}>باز کردن گام بعدی</Text>
              <ChevronLeft size={16} color={colors.primary} />
            </Pressable>
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={270}>
        <SectionHeader
          title="نمای امروز"
          action={
            <Pressable accessibilityRole="button" onPress={() => onNavigate("statistics")}>
              <Text style={styles.sectionAction}>تحلیل کامل</Text>
            </Pressable>
          }
        />
        <LearningCard tone="blue" style={styles.insightCard}>
          <Image source={require("../../assets/illustrations/analytics-reports.png")} style={styles.insightImage} />
          <View style={styles.insightCopy}>
            <Text style={styles.insightValue}>{summary.accuracy_percent}%</Text>
            <Text style={styles.insightLabel}>دقت فعلی</Text>
            <Text style={styles.insightMeta}>
              {activity.completed_quizzes} آزمون کامل · {activity.flashcard_reviews} مرور کارت · {activity.total_study_minutes} دقیقه
            </Text>
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={320}>
        <SectionHeader title="نقاطی برای تقویت" />
        {summary.weak_topics.length ? (
          summary.weak_topics.slice(0, 3).map((topic) => (
            <Pressable key={topic.topic_key} accessibilityRole="button" onPress={() => onNavigate("mistakes")}>
              <LearningCard tone="rose" style={styles.topicCard}>
                <View style={styles.topicIcon}>
                  <AlertTriangle size={18} color={featureAccents.mistakes.color} />
                </View>
                <View style={styles.topicCopy}>
                  <Text style={styles.topicTitle}>{topic.topic_label}</Text>
                  <Text style={styles.topicMeta}>{topic.wrong_answers} نکته برای مرور</Text>
                </View>
                <Text style={styles.topicScore}>{topic.accuracy_percent}%</Text>
              </LearningCard>
            </Pressable>
          ))
        ) : (
          <LearningCard tone="sage" style={styles.clearCard}>
            <Sparkles size={20} color={colors.primary} />
            <View style={styles.topicCopy}>
              <Text style={styles.topicTitle}>مسیرت صاف است</Text>
              <Text style={styles.topicMeta}>فعلاً موضوع ضعیف برجسته‌ای برای مرور نداری.</Text>
            </View>
          </LearningCard>
        )}
      </AnimatedEntrance>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  topbar: {
    minHeight: 58,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    marginBottom: spacing.md,
  },
  skeletonTopbar: {
    marginBottom: spacing.md,
  },
  skeletonTopbarItem: {
    width: "100%",
  },
  skeletonQuickGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  skeletonQuickItem: {
    width: "31.5%",
  },
  topActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.06)",
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
    fontSize: 26,
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
    width: 210,
    height: 210,
    borderRadius: radius.pill,
    backgroundColor: "rgba(32,242,138,0.14)",
    top: -105,
    right: -78,
  },
  heroTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  heroCopy: {
    flex: 1,
    paddingRight: spacing.xs,
  },
  todayPill: {
    alignSelf: "flex-start",
    minHeight: 28,
    borderRadius: radius.pill,
    backgroundColor: "rgba(3,24,32,0.42)",
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
  },
  heroTitle: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: -0.45,
  },
  heroMeta: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 21,
    marginTop: spacing.xs,
  },
  heroIllustration: {
    marginLeft: -8,
  },
  journeyTrack: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  journeyStep: {
    width: 68,
    alignItems: "center",
  },
  journeyDot: {
    width: 28,
    height: 28,
    borderRadius: radius.pill,
    backgroundColor: "rgba(3,24,32,0.52)",
    borderWidth: 1,
    borderColor: colors.borderStrong,
    alignItems: "center",
    justifyContent: "center",
  },
  journeyDotComplete: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  journeyNumber: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "900",
  },
  journeyNumberComplete: {
    color: colors.black,
  },
  journeyLabel: {
    color: colors.ink,
    fontSize: 10,
    fontWeight: "900",
    marginTop: spacing.xs,
  },
  journeyDetail: {
    color: colors.muted,
    fontSize: 9,
    fontWeight: "700",
    marginTop: 2,
    textAlign: "center",
  },
  journeyLine: {
    flex: 1,
    height: 2,
    marginTop: 13,
    backgroundColor: "rgba(255,255,255,0.14)",
  },
  journeyLineComplete: {
    backgroundColor: colors.primary,
  },
  heroFooter: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: spacing.lg,
  },
  metricRow: {
    flex: 1,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  heroAction: {
    minWidth: 136,
  },
  quickGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: spacing.sm,
  },
  quickCard: {
    width: "31.5%",
    minHeight: 126,
    borderRadius: radius.lg,
    backgroundColor: "rgba(10,39,49,0.88)",
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.sm,
    marginBottom: spacing.sm,
  },
  pressed: {
    transform: [{scale: 0.97}],
    opacity: 0.92,
  },
  quickIcon: {
    width: 52,
    height: 52,
    borderRadius: radius.md,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.sm,
  },
  quickIllustration: {
    width: 42,
    height: 42,
  },
  quickTitle: {
    fontSize: 12,
    fontWeight: "900",
  },
  quickMeta: {
    color: colors.muted,
    fontSize: 9,
    fontWeight: "700",
    marginTop: 3,
  },
  sectionAction: {
    color: colors.primary,
    fontSize: typography.small,
    fontWeight: "900",
  },
  achievementsScroller: {
    gap: spacing.sm,
    paddingBottom: spacing.sm,
  },
  achievementCard: {
    width: 236,
    minHeight: 104,
    marginBottom: 0,
    padding: spacing.md,
    flexDirection: "row",
    alignItems: "center",
  },
  achievementLocked: {
    opacity: 0.56,
  },
  achievementBadge: {
    width: 62,
    height: 62,
    borderRadius: radius.lg,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  achievementImage: {
    width: 50,
    height: 50,
  },
  achievementCopy: {
    flex: 1,
    marginLeft: spacing.md,
  },
  achievementTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  achievementTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  achievementMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  storyCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceElevated,
    overflow: "hidden",
  },
  storyIllustrationWrap: {
    width: 104,
    height: 104,
    borderRadius: radius.lg,
    backgroundColor: colors.secondarySoft,
    alignItems: "center",
    justifyContent: "center",
  },
  storyIllustration: {
    width: 94,
    height: 94,
  },
  storyCopy: {
    flex: 1,
    marginLeft: spacing.md,
  },
  storyEyebrow: {
    color: colors.secondary,
    fontSize: 10,
    fontWeight: "900",
  },
  storyTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "900",
    marginTop: spacing.xs,
  },
  storyMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  storyLink: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    marginTop: spacing.sm,
  },
  storyLinkText: {
    color: colors.primary,
    fontSize: typography.small,
    fontWeight: "900",
  },
  insightCard: {
    flexDirection: "row",
    alignItems: "center",
  },
  insightImage: {
    width: 100,
    height: 100,
  },
  insightCopy: {
    flex: 1,
    marginLeft: spacing.md,
  },
  insightValue: {
    color: colors.ink,
    fontSize: 31,
    fontWeight: "900",
  },
  insightLabel: {
    color: colors.blue,
    fontWeight: "900",
  },
  insightMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    lineHeight: 20,
    marginTop: spacing.sm,
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
    backgroundColor: featureAccents.mistakes.soft,
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
    color: featureAccents.mistakes.color,
    fontSize: typography.heading,
    fontWeight: "900",
    marginLeft: spacing.md,
  },
});
