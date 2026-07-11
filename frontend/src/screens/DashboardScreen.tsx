import React, {useCallback, useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {
  AlertTriangle,
  BarChart3,
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

import {platformApi} from "../api/platform";
import {InstallPrompt} from "../components/InstallPrompt";
import {
  AnimatedEntrance,
  Avatar,
  BrandMark,
  ErrorState,
  LearningCard,
  LoadingState,
  MetricPill,
  PrimaryButton,
  ProgressBar,
  ProgressRing,
  ScreenContainer,
  SectionHeader,
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
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setDashboard(await platformApi.dashboard(token));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Dashboard unavailable.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="Loading dashboard" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!dashboard) return null;

  const summary = dashboard.summary;
  const reviewCount = summary.due_flashcards;
  const relearnCount = summary.mistake_count;
  const learnCount = Math.max(5, 10 - Math.min(5, reviewCount));
  const totalActions = learnCount + reviewCount + relearnCount;
  const estimatedMinutes = Math.max(10, Math.round(learnCount * 1.5 + reviewCount * 2 + relearnCount * 1.2));
  const nextAction: ScreenKey = reviewCount > 0 ? "flashcards" : relearnCount > 0 ? "mistakes" : "quiz";
  const nextActionLabel = reviewCount > 0 ? "Start review" : relearnCount > 0 ? "Fix mistakes" : "Start quiz";
  const quickActions: QuickAction[] = [
    {key: "quiz", label: "Quiz", meta: `${learnCount} new`, Icon: Brain, color: colors.primary},
    {key: "flashcards", label: "Review", meta: `${reviewCount} due`, Icon: Layers, color: colors.secondary},
    {key: "mistakes", label: "Relearn", meta: `${relearnCount} items`, Icon: RotateCcw, color: colors.rose},
    {key: "league", label: "League", meta: `#${dashboard.league.rank ?? "-"}`, Icon: Trophy, color: colors.amber},
  ];

  return (
    <ScreenContainer>
      <View style={styles.topbar}>
        <BrandMark />
        <View style={styles.topActions}>
          <Pressable accessibilityRole="button" onPress={load} style={styles.iconButton}>
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
          <Text style={styles.welcome}>Welcome back, {user?.username ?? "learner"}!</Text>
          <Text style={styles.welcomeMeta}>Ready to level up your clinical knowledge?</Text>
        </View>
      </AnimatedEntrance>

      <AnimatedEntrance delay={70}>
        <LearningCard tone="primary" style={styles.hero}>
          <View pointerEvents="none" style={styles.heroGlow} />
          <View style={styles.heroContent}>
            <View style={styles.heroCopy}>
              <View style={styles.todayPill}>
                <Sparkles size={14} color={colors.primary} />
                <Text style={styles.todayPillText}>TODAY'S MISSION</Text>
              </View>
              <Text style={styles.heroTitle}>{nextActionLabel}</Text>
              <Text style={styles.heroMeta}>
                {estimatedMinutes} min · {totalActions} focused actions
              </Text>
              <View style={styles.metricRow}>
                <MetricPill label="XP" value={summary.xp} Icon={Target} />
                <MetricPill label="streak" value={summary.current_streak} Icon={Flame} />
              </View>
            </View>
            <ProgressRing value={summary.accuracy_percent} label="accuracy" size={112} />
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
          title="Next up"
          action={
            <Pressable onPress={() => onNavigate("planning")}>
              <Text style={styles.sectionAction}>Edit plan</Text>
            </Pressable>
          }
        />
        <LearningCard style={styles.eventCard}>
          <View style={styles.eventTop}>
            <View style={styles.eventIcon}>
              <CalendarCheck size={22} color={colors.black} />
            </View>
            <View style={styles.eventCopy}>
              <Text style={styles.eventEyebrow}>PERSONAL LEARNING ROUTE</Text>
              <Text style={styles.eventTitle}>
                {dashboard.recommendations[0]?.title ?? "Keep your learning streak alive"}
              </Text>
              <Text style={styles.eventMeta}>
                {dashboard.recommendations[0]?.reason ?? "Complete one focused session today."}
              </Text>
            </View>
          </View>
          <View style={styles.eventFooter}>
            <MetricPill label="minutes" value={estimatedMinutes} />
            <MetricPill label="actions" value={totalActions} />
            <Pressable style={styles.eventJoin} onPress={() => onNavigate(nextAction)}>
              <Text style={styles.eventJoinText}>Open</Text>
            </Pressable>
          </View>
        </LearningCard>
      </AnimatedEntrance>

      <AnimatedEntrance delay={220}>
        <SectionHeader
          title="Performance"
          action={
            <Pressable onPress={() => onNavigate("statistics")}>
              <Text style={styles.sectionAction}>View all</Text>
            </Pressable>
          }
        />
        <View style={styles.performanceGrid}>
          <LearningCard tone="blue" style={styles.performanceCard}>
            <BarChart3 size={22} color={colors.blue} />
            <Text style={styles.performanceValue}>{summary.accuracy_percent}%</Text>
            <Text style={styles.performanceLabel}>Accuracy</Text>
          </LearningCard>
          <LearningCard tone="amber" style={styles.performanceCard}>
            <Trophy size={22} color={colors.amber} />
            <Text style={styles.performanceValue}>#{dashboard.league.rank ?? "-"}</Text>
            <Text style={styles.performanceLabel}>League rank</Text>
          </LearningCard>
        </View>
      </AnimatedEntrance>

      <SectionHeader title="Focus areas" />
      {summary.weak_topics.length ? (
        summary.weak_topics.slice(0, 3).map((topic) => (
          <Pressable key={topic.topic_key} onPress={() => onNavigate("mistakes")}>
            <LearningCard tone="rose" style={styles.topicCard}>
              <View style={styles.topicIcon}>
                <AlertTriangle size={18} color={colors.rose} />
              </View>
              <View style={styles.topicCopy}>
                <Text style={styles.topicTitle}>{topic.topic_label}</Text>
                <Text style={styles.topicMeta}>{topic.wrong_answers} mistakes to revisit</Text>
              </View>
              <Text style={styles.topicScore}>{topic.accuracy_percent}%</Text>
            </LearningCard>
          </Pressable>
        ))
      ) : (
        <LearningCard tone="sage" style={styles.clearCard}>
          <Sparkles size={20} color={colors.primary} />
          <View style={styles.topicCopy}>
            <Text style={styles.topicTitle}>All clear</Text>
            <Text style={styles.topicMeta}>No weak-topic signal in your current progress.</Text>
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
  performanceGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  performanceCard: {
    width: "48%",
    minHeight: 138,
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
