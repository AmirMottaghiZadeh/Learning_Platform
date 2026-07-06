import React, {useCallback, useEffect, useState} from "react";
import {StyleSheet, Text, View} from "react-native";
import {Medal, RefreshCw, Trophy} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {EmptyState, ErrorState, LearningCard, LoadingState, ScreenContainer, ScreenHeader, SecondaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {LeaderboardEntry, LeagueFullSummary, MyLeagueRank} from "../types/api";

export function LeagueScreen() {
  const {token} = useAuth();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [myRank, setMyRank] = useState<MyLeagueRank | null>(null);
  const [summary, setSummary] = useState<LeagueFullSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const payload = await platformApi.leagueSummary(token);
      setSummary(payload);
      setEntries(payload.leaderboard);
      setMyRank(payload.my_rank);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "League unavailable.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="Loading league" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={summary?.season_key ? `Weekly season · ${summary.season_key}` : "Weekly season"}
        title="League"
        action={<SecondaryButton label="Refresh" Icon={RefreshCw} onPress={load} />}
      />

      <LearningCard tone="amber">
        <View style={styles.rankTop}>
          <View style={styles.trophy}>
            <Trophy size={24} color={colors.amber} />
          </View>
          <View style={styles.rankText}>
            <Text style={styles.rankLabel}>My rank</Text>
            <Text style={styles.rankValue}>{myRank?.rank ?? "-"}</Text>
          </View>
          <Text style={styles.participants}>{myRank?.total_participants ?? 0} learners</Text>
        </View>
        {summary?.rule_version ? <Text style={styles.ruleVersion}>{summary.rule_version}</Text> : null}
      </LearningCard>

      {!entries.length ? (
        <EmptyState title="No league results" />
      ) : (
        entries.map((entry) => (
          <LearningCard key={`${entry.rank}-${entry.result.id}`}>
            <View style={styles.row}>
              <View style={styles.rankPill}>
                <Medal size={16} color={colors.primary} />
                <Text style={styles.rankNumber}>{entry.rank}</Text>
              </View>
              <View style={styles.userBlock}>
                <Text style={styles.username}>{entry.result.username}</Text>
                <Text style={styles.meta}>{entry.result.topic_key}</Text>
              </View>
              <View style={styles.scoreBlock}>
                <Text style={styles.score}>{entry.result.league_rating}</Text>
                <Text style={styles.meta}>{entry.result.percent}%</Text>
              </View>
            </View>
          </LearningCard>
        ))
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  rankTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  trophy: {
    width: 52,
    height: 52,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  rankText: {
    flex: 1,
  },
  rankLabel: {
    color: colors.muted,
    fontWeight: "800",
  },
  rankValue: {
    color: colors.ink,
    fontSize: 28,
    fontWeight: "900",
  },
  participants: {
    color: colors.ink,
    fontWeight: "900",
  },
  ruleVersion: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.sm,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  rankPill: {
    minWidth: 58,
    minHeight: 40,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  rankNumber: {
    color: colors.primary,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  userBlock: {
    flex: 1,
  },
  username: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  meta: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  scoreBlock: {
    alignItems: "flex-end",
  },
  score: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
});
