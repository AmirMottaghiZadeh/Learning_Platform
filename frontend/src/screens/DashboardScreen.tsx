import React, {useCallback, useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {BarChart3, Brain, Flame, Layers, RefreshCw, Sparkles, Target, Trophy} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {LearningCard, LoadingState, ErrorState, ProgressBar, ScreenContainer, ScreenHeader, SectionTitle, StatTile} from "../components/ui";
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

      <LearningCard tone="mint">
        <View style={styles.heroTop}>
          <View style={styles.heroIcon}>
            <Sparkles size={24} color={colors.primary} />
          </View>
          <View style={styles.heroTextWrap}>
            <Text style={styles.heroTitle}>Today's learning plan</Text>
            <Text style={styles.heroMeta}>Accuracy {summary.accuracy_percent}% · {summary.due_flashcards} cards due</Text>
          </View>
        </View>
        <ProgressBar value={summary.accuracy_percent} />
        <View style={styles.heroStats}>
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatValue}>{summary.xp}</Text>
            <Text style={styles.heroStatLabel}>XP</Text>
          </View>
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatValue}>{summary.current_streak}</Text>
            <Text style={styles.heroStatLabel}>Streak</Text>
          </View>
        </View>
        <View style={styles.quickRow}>
          <Pressable style={styles.quickAction} onPress={() => onNavigate("quiz")}>
            <Brain size={18} color={colors.ink} />
            <Text style={styles.quickText}>Quiz</Text>
          </Pressable>
          <Pressable style={styles.quickAction} onPress={() => onNavigate("flashcards")}>
            <Layers size={18} color={colors.ink} />
            <Text style={styles.quickText}>Review</Text>
          </Pressable>
        </View>
      </LearningCard>

      <View style={styles.statGrid}>
        <StatTile label="XP" value={summary.xp} Icon={Target} tone="mint" />
        <StatTile label="Streak" value={summary.current_streak} Icon={Flame} tone="rose" />
        <StatTile label="Due cards" value={summary.due_flashcards} Icon={Layers} tone="blue" />
        <StatTile label="League rank" value={dashboard.league.rank ?? "-"} Icon={Trophy} tone="lavender" />
      </View>

      <SectionTitle>Recommendations</SectionTitle>
      {dashboard.recommendations.map((item) => (
        <LearningCard key={item.id}>
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
    fontSize: typography.heading,
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
