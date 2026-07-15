import React, {useCallback, useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {Crown, RefreshCw, Trophy} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {
  Avatar,
  EmptyState,
  ErrorState,
  LearningCard,
  LoadingState,
  MetricPill,
  ScreenContainer,
  ScreenHeader,
} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {LeaderboardEntry, LeagueFullSummary, MyLeagueRank} from "../types/api";

function topicLabel(topicKey: string) {
  if (topicKey === "brandGeneric") return "نام تجاری";
  if (topicKey === "timing") return "با غذا / بی غذا";
  if (topicKey === "indication") return "اندیکاسیون";
  if (topicKey === "sideEffects") return "عوارض";
  if (topicKey === "dosing") return "دوزینگ";
  return "ترکیبی";
}

export function LeagueScreen() {
  const {token, user} = useAuth();
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
      setError(exc instanceof Error ? exc.message : "بارگذاری لیگ ممکن نیست.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="در حال بارگذاری لیگ" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const podiumEntries = entries.slice(0, 3);
  const podiumOrder = [podiumEntries[1], podiumEntries[0], podiumEntries[2]].filter(Boolean);

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={summary?.season_key ? `فصل هفتگی · ${summary.season_key}` : "فصل هفتگی"}
        title="جدول رتبه‌بندی"
        action={
          <Pressable accessibilityRole="button" onPress={load} style={styles.refresh}>
            <RefreshCw size={18} color={colors.primary} />
          </Pressable>
        }
      />

      <LearningCard tone="primary" style={styles.hero}>
        <View style={styles.heroTop}>
          <View>
            <Text style={styles.heroEyebrow}>رتبه شما</Text>
            <Text style={styles.heroRank}>#{myRank?.rank ?? "-"}</Text>
          </View>
          <View style={styles.heroMetrics}>
            <MetricPill label="کاربر" value={myRank?.total_participants ?? 0} />
            <MetricPill label="فصل" value="هفتگی" />
          </View>
        </View>
        <Text style={styles.heroText}>هر تمرین متمرکز، شما را به صدر جدول نزدیک‌تر می‌کند.</Text>
      </LearningCard>

      {podiumOrder.length ? (
        <View style={styles.podium}>
          {podiumOrder.map((entry) => {
            const isWinner = entry.rank === 1;
            return (
              <View key={`${entry.rank}-${entry.result.id}`} style={[styles.podiumItem, isWinner && styles.podiumWinner]}>
                {isWinner ? <Crown size={21} color={colors.amber} style={styles.crown} /> : null}
                <View style={[styles.avatarRing, isWinner && styles.avatarRingWinner]}>
                  <Avatar name={entry.result.username} size={isWinner ? 66 : 54} />
                </View>
                <Text style={styles.podiumName} numberOfLines={1}>{entry.result.username}</Text>
                <Text style={styles.podiumScore}>{entry.result.league_rating} امتیاز لیگ</Text>
                <View style={[styles.podiumBlock, isWinner && styles.podiumBlockWinner]}>
                  <Text style={[styles.podiumRank, isWinner && styles.podiumRankWinner]}>{entry.rank}</Text>
                </View>
              </View>
            );
          })}
        </View>
      ) : null}

      {!entries.length ? (
        <EmptyState title="نتیجه‌ای برای لیگ ثبت نشده است" />
      ) : (
        <View style={styles.list}>
          {entries.map((entry) => {
            const isCurrentUser = entry.result.username === user?.username;
            return (
              <View
                key={`${entry.rank}-${entry.result.id}`}
                style={[styles.row, isCurrentUser && styles.currentRow]}
              >
                <View style={[styles.rankBadge, entry.rank <= 3 && styles.topRankBadge]}>
                  <Text style={[styles.rankNumber, entry.rank <= 3 && styles.topRankNumber]}>{entry.rank}</Text>
                </View>
                <Avatar name={entry.result.username} size={42} />
                <View style={styles.userBlock}>
                  <Text style={styles.username}>
                    {entry.result.username}{isCurrentUser ? " (شما)" : ""}
                  </Text>
                  <Text style={styles.meta}>{topicLabel(entry.result.topic_key)} · {entry.result.percent}% دقت</Text>
                </View>
                <View style={styles.scoreBlock}>
                  <Text style={styles.score}>{entry.result.league_rating}</Text>
                  <Text style={styles.meta}>امتیاز</Text>
                </View>
              </View>
            );
          })}
        </View>
      )}

      {summary?.rule_version ? (
        <View style={styles.rules}>
          <Trophy size={16} color={colors.muted} />
          <Text style={styles.ruleText}>نسخه قوانین لیگ: {summary.rule_version}</Text>
        </View>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  refresh: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  hero: {
    backgroundColor: colors.surfaceElevated,
  },
  heroTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  heroEyebrow: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.8,
  },
  heroRank: {
    color: colors.ink,
    fontSize: 34,
    fontWeight: "900",
  },
  heroMetrics: {
    alignItems: "flex-end",
    gap: spacing.sm,
  },
  heroText: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.md,
  },
  podium: {
    minHeight: 230,
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "center",
    marginTop: spacing.lg,
    marginBottom: spacing.xl,
  },
  podiumItem: {
    width: "31%",
    alignItems: "center",
  },
  podiumWinner: {
    marginBottom: spacing.lg,
  },
  crown: {
    marginBottom: spacing.xs,
  },
  avatarRing: {
    borderRadius: radius.pill,
    borderWidth: 2,
    borderColor: colors.borderStrong,
    padding: 3,
  },
  avatarRingWinner: {
    borderColor: colors.primary,
  },
  podiumName: {
    maxWidth: "92%",
    color: colors.ink,
    fontSize: typography.small,
    fontWeight: "900",
    marginTop: spacing.sm,
  },
  podiumScore: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: 2,
  },
  podiumBlock: {
    width: "88%",
    minHeight: 60,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.sm,
  },
  podiumBlockWinner: {
    minHeight: 86,
    backgroundColor: colors.primary,
  },
  podiumRank: {
    color: colors.ink,
    fontSize: 25,
    fontWeight: "900",
  },
  podiumRankWinner: {
    color: colors.black,
  },
  list: {
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  row: {
    minHeight: 74,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  currentRow: {
    backgroundColor: colors.primarySoft,
  },
  rankBadge: {
    width: 34,
    height: 34,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.sm,
  },
  topRankBadge: {
    backgroundColor: colors.primary,
  },
  rankNumber: {
    color: colors.muted,
    fontWeight: "900",
  },
  topRankNumber: {
    color: colors.black,
  },
  userBlock: {
    flex: 1,
    marginLeft: spacing.md,
  },
  username: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  meta: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    marginTop: 2,
  },
  scoreBlock: {
    alignItems: "flex-end",
    marginLeft: spacing.sm,
  },
  score: {
    color: colors.primary,
    fontSize: 17,
    fontWeight: "900",
  },
  rules: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.lg,
  },
  ruleText: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    marginLeft: spacing.sm,
  },
});
