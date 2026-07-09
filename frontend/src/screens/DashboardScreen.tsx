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
  SearchCheck,
  Sparkles,
  Target,
  Trophy,
} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {InstallPrompt} from "../components/InstallPrompt";
import {
  LearningCard,
  LoadingState,
  ErrorState,
  ProgressBar,
  PrimaryButton,
  ScreenContainer,
  ScreenHeader,
  SectionTitle,
  StatTile,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";
import {useAuth} from "../store/auth";
import type {Dashboard} from "../types/api";

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
  const estimatedMinutes = Math.max(10, Math.round(learnCount * 1.5 + reviewCount * 2 + relearnCount * 1.2));
  const nextAction: ScreenKey = reviewCount > 0 ? "flashcards" : relearnCount > 0 ? "mistakes" : "quiz";
  const nextActionLabel = reviewCount > 0 ? "Start review" : relearnCount > 0 ? "Fix mistakes" : "Start quiz";

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={`Clinical learning · ${user?.username ?? "learner"}`}
        title="K_Game"
        action={
          <Pressable accessibilityRole="button" onPress={load} style={styles.refresh}>
            <RefreshCw size={18} color={colors.primary} />
          </Pressable>
        }
      />
      <InstallPrompt />

      <LearningCard tone="mint">
        <View style={styles.heroTop}>
          <View style={styles.heroIcon}>
            <Sparkles size={24} color={colors.primary} />
          </View>
          <View style={styles.heroTextWrap}>
            <Text style={styles.heroTitle}>Today's exact plan</Text>
            <Text style={styles.heroMeta}>
              {estimatedMinutes} min · {learnCount + reviewCount + relearnCount} learning actions
            </Text>
          </View>
        </View>
        <ProgressBar value={summary.accuracy_percent} />
        <Text style={styles.guidance}>Focus on the next best action, then let the loop update from backend progress.</Text>
        <View style={styles.heroStats}>
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatValue}>{learnCount}</Text>
            <Text style={styles.heroStatLabel}>Learn</Text>
          </View>
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatValue}>{reviewCount}</Text>
            <Text style={styles.heroStatLabel}>Review</Text>
          </View>
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatValue}>{relearnCount}</Text>
            <Text style={styles.heroStatLabel}>Relearn</Text>
          </View>
        </View>
        <PrimaryButton label={nextActionLabel} Icon={Sparkles} onPress={() => onNavigate(nextAction)} />
      </LearningCard>

      <SectionTitle>Learning cycle</SectionTitle>
      <View style={styles.loopGrid}>
        <LearningCard tone="blue" style={styles.loopCard}>
          <Brain size={22} color={colors.primary} />
          <Text style={styles.loopTitle}>Learn</Text>
          <Text style={styles.loopMeta}>{learnCount} new prompts</Text>
        </LearningCard>
        <LearningCard tone="mint" style={styles.loopCard}>
          <Layers size={22} color={colors.primary} />
          <Text style={styles.loopTitle}>Review</Text>
          <Text style={styles.loopMeta}>{reviewCount} due cards</Text>
        </LearningCard>
        <LearningCard tone="rose" style={styles.loopCard}>
          <RotateCcw size={22} color={colors.primary} />
          <Text style={styles.loopTitle}>Relearn</Text>
          <Text style={styles.loopMeta}>{relearnCount} mistakes</Text>
        </LearningCard>
        <LearningCard tone="lavender" style={styles.loopCard}>
          <SearchCheck size={22} color={colors.primary} />
          <Text style={styles.loopTitle}>Check</Text>
          <Text style={styles.loopMeta}>{summary.accuracy_percent}% accuracy</Text>
        </LearningCard>
      </View>

      <View style={styles.statGrid}>
        <StatTile label="XP" value={summary.xp} Icon={Target} tone="mint" />
        <StatTile label="Streak" value={summary.current_streak} Icon={Flame} tone="rose" />
        <StatTile label="Due cards" value={summary.due_flashcards} Icon={Layers} tone="blue" />
        <StatTile label="League rank" value={dashboard.league.rank ?? "-"} Icon={Trophy} tone="lavender" />
      </View>

      <SectionTitle>Recommendations</SectionTitle>
      {dashboard.recommendations.map((item) => (
        <LearningCard key={item.id} tone="plain">
          <View style={styles.recommendationTop}>
            <AlertTriangle size={18} color={colors.primary} />
            <Text style={styles.priority}>Priority {item.priority}</Text>
          </View>
          <Text style={styles.cardTitle}>{item.title}</Text>
          <Text style={styles.cardMeta}>{item.reason}</Text>
        </LearningCard>
      ))}

      <SectionTitle>Weak topics</SectionTitle>
      {summary.weak_topics.length ? (
        summary.weak_topics.map((topic) => (
          <LearningCard key={topic.topic_key} tone="rose">
            <View style={styles.topicRow}>
              <View style={styles.topicText}>
                <Text style={styles.cardTitle}>{topic.topic_label}</Text>
                <Text style={styles.cardMeta}>{topic.wrong_answers} mistakes</Text>
              </View>
              <Text style={styles.topicScore}>{topic.accuracy_percent}%</Text>
            </View>
          </LearningCard>
        ))
      ) : (
        <LearningCard tone="sage">
          <Text style={styles.cardTitle}>No weak topics</Text>
          <Text style={styles.cardMeta}>Progress data is clear.</Text>
        </LearningCard>
      )}

      <Pressable style={styles.statsLink} onPress={() => onNavigate("statistics")}>
        <BarChart3 size={18} color={colors.primary} />
        <Text style={styles.statsText}>Open statistics</Text>
      </Pressable>
      <Pressable style={styles.statsLink} onPress={() => onNavigate("planning")}>
        <CalendarCheck size={18} color={colors.primary} />
        <Text style={styles.statsText}>Adjust study plan</Text>
      </Pressable>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  refresh: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  heroTop: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  heroIcon: {
    width: 52,
    height: 52,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  heroTextWrap: {
    flex: 1,
  },
  heroTitle: {
    color: colors.ink,
    fontSize: 23,
    fontWeight: "900",
  },
  heroMeta: {
    color: colors.muted,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  guidance: {
    color: colors.muted,
    fontWeight: "800",
    lineHeight: 22,
    marginTop: spacing.md,
  },
  quickRow: {
    flexDirection: "row",
    marginTop: spacing.lg,
    gap: spacing.sm,
  },
  quickAction: {
    flex: 1,
    minHeight: 48,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    borderWidth: 1,
    borderColor: colors.border,
  },
  quickText: {
    color: colors.ink,
    fontWeight: "900",
    marginLeft: spacing.sm,
  },
  statGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  heroStats: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  heroStatPill: {
    minHeight: 46,
    flex: 1,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    justifyContent: "center",
  },
  heroStatValue: {
    color: colors.ink,
    fontWeight: "900",
    fontSize: 18,
  },
  heroStatLabel: {
    color: colors.muted,
    fontWeight: "800",
    fontSize: typography.small,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  loopGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  loopCard: {
    width: "48%",
    minHeight: 136,
  },
  loopTitle: {
    color: colors.ink,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  loopMeta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  recommendationTop: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  priority: {
    color: colors.primary,
    fontSize: typography.small,
    fontWeight: "900",
    marginLeft: spacing.sm,
  },
  cardMeta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
    lineHeight: 20,
  },
  topicRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  topicText: {
    flex: 1,
  },
  topicScore: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  statsLink: {
    minHeight: 52,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.sm,
  },
  statsText: {
    color: colors.primary,
    fontWeight: "900",
    marginLeft: spacing.sm,
  },
});
