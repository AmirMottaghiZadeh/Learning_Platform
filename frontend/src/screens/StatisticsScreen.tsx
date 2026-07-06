import React, {useCallback, useEffect, useState} from "react";
import {StyleSheet, Text, View} from "react-native";
import {Activity, BarChart3, CheckCircle2, RefreshCw, Target} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {ErrorState, LearningCard, LoadingState, ProgressBar, ScreenContainer, ScreenHeader, SectionTitle, SecondaryButton, StatTile} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {Statistics} from "../types/api";

export function StatisticsScreen() {
  const {token} = useAuth();
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setStatistics(await platformApi.statistics(token));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Statistics unavailable.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="Loading statistics" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!statistics) return null;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow="Progress"
        title="Statistics"
        action={<SecondaryButton label="Refresh" Icon={RefreshCw} onPress={load} />}
      />

      <View style={styles.statGrid}>
        <StatTile label="Answered" value={statistics.summary.questions_answered} Icon={Activity} tone="blue" />
        <StatTile label="Accuracy" value={`${statistics.summary.accuracy_percent}%`} Icon={CheckCircle2} tone="sage" />
        <StatTile label="XP" value={statistics.summary.xp} Icon={Target} tone="amber" />
        <StatTile label="Reviews" value={statistics.summary.review_count} Icon={BarChart3} tone="primary" />
      </View>

      <SectionTitle>Daily activity</SectionTitle>
      <LearningCard>
        {statistics.daily_activity.map((day) => {
          const total = day.questions_answered + day.reviews_completed + day.mistakes_created;
          return (
            <View key={day.date} style={styles.dayRow}>
              <Text style={styles.dayLabel}>{day.date.slice(5)}</Text>
              <View style={styles.dayBarWrap}>
                <ProgressBar value={Math.min(100, total * 18)} />
              </View>
              <Text style={styles.dayValue}>{total}</Text>
            </View>
          );
        })}
      </LearningCard>

      <SectionTitle>Topics</SectionTitle>
      {statistics.topics.map((topic) => (
        <LearningCard key={topic.id}>
          <View style={styles.topicTop}>
            <Text style={styles.topicTitle}>{topic.topic_label}</Text>
            <Text style={styles.topicPercent}>{topic.accuracy_percent}%</Text>
          </View>
          <ProgressBar value={topic.accuracy_percent} />
          <Text style={styles.topicMeta}>
            {topic.questions_answered} answered · {topic.mastery_state}
          </Text>
        </LearningCard>
      ))}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  statGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  dayRow: {
    minHeight: 36,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  dayLabel: {
    width: 52,
    color: colors.muted,
    fontWeight: "900",
  },
  dayBarWrap: {
    flex: 1,
  },
  dayValue: {
    width: 32,
    color: colors.ink,
    fontWeight: "900",
    textAlign: "right",
  },
  topicTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  topicTitle: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
    flex: 1,
  },
  topicPercent: {
    color: colors.primary,
    fontSize: typography.heading,
    fontWeight: "900",
    marginLeft: spacing.md,
  },
  topicMeta: {
    color: colors.muted,
    fontWeight: "800",
    marginTop: spacing.md,
  },
});
