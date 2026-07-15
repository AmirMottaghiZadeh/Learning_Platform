import React from "react";
import {StyleSheet, Text, View} from "react-native";
import {Activity, BarChart3, CheckCircle2, RefreshCw, Target} from "lucide-react-native";
import {useQuery} from "@tanstack/react-query";

import {platformApi} from "../api/platform";
import {ErrorState, LearningCard, LoadingState, ProgressBar, ScreenContainer, ScreenHeader, SectionTitle, SecondaryButton, StatTile} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {Statistics} from "../types/api";

function masteryLabel(value: string) {
  if (value === "mastered") return "مسلط";
  if (value === "reviewing") return "در حال مرور";
  if (value === "practicing") return "در حال تمرین";
  if (value === "seen") return "دیده‌شده";
  return "شروع‌نشده";
}

export function StatisticsScreen() {
  const {token} = useAuth();
  const statisticsQuery = useQuery({
    queryKey: ["statistics", token],
    queryFn: () => platformApi.statistics(token!),
    enabled: Boolean(token),
  });

  if (statisticsQuery.isLoading) return <LoadingState label="در حال بارگذاری آمار" />;
  if (statisticsQuery.error) {
    return (
      <ErrorState
        message={statisticsQuery.error instanceof Error ? statisticsQuery.error.message : "بارگذاری آمار ممکن نیست."}
        onRetry={() => statisticsQuery.refetch()}
      />
    );
  }
  const statistics = statisticsQuery.data as Statistics | undefined;
  if (!statistics) return null;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={`${statistics.start_date} تا ${statistics.end_date}`}
        title="آمار"
        action={<SecondaryButton label="بروزرسانی" Icon={RefreshCw} onPress={() => statisticsQuery.refetch()} />}
      />

      <View style={styles.statGrid}>
        <StatTile label="پاسخ داده‌شده" value={statistics.summary.questions_answered} Icon={Activity} tone="blue" />
        <StatTile label="دقت" value={`${statistics.summary.accuracy_percent}%`} Icon={CheckCircle2} tone="sage" />
        <StatTile label="امتیاز" value={statistics.summary.xp} Icon={Target} tone="amber" />
        <StatTile label="مرور" value={statistics.summary.review_count} Icon={BarChart3} tone="lavender" />
      </View>

      <SectionTitle>خلاصه فعالیت</SectionTitle>
      <LearningCard tone="blue">
        <Text style={styles.topicMeta}>آزمون کامل‌شده: {statistics.activity_summary.completed_quizzes}</Text>
        <Text style={styles.topicMeta}>فلش‌کارت مرورشده: {statistics.activity_summary.flashcard_reviews}</Text>
        <Text style={styles.topicMeta}>یادآوری ذخیره‌شده: {statistics.activity_summary.saved_reminders}</Text>
        <Text style={styles.topicMeta}>زمان مطالعه: {statistics.activity_summary.total_study_minutes} دقیقه</Text>
      </LearningCard>

      <SectionTitle>فعالیت روزانه</SectionTitle>
      <LearningCard tone="mint">
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

      <SectionTitle>موضوعات ضعیف</SectionTitle>
      {statistics.weak_topics.length ? (
        statistics.weak_topics.map((topic) => (
          <LearningCard key={topic.topic_key} tone="rose">
            <View style={styles.topicTop}>
              <Text style={styles.topicTitle}>{topic.topic_label}</Text>
              <Text style={styles.topicPercent}>{topic.accuracy_percent}%</Text>
            </View>
            <ProgressBar value={topic.accuracy_percent} />
          <Text style={styles.topicMeta}>
              {topic.wrong_answers} غلط · {topic.due_flashcards} کارت در انتظار · {masteryLabel(topic.mastery_state)}
            </Text>
          </LearningCard>
        ))
      ) : (
        <LearningCard tone="sage">
          <Text style={styles.topicTitle}>موضوع ضعیفی دیده نمی‌شود</Text>
          <Text style={styles.topicMeta}>در وضعیت فعلی، سیگنال ضعیف برجسته‌ای وجود ندارد.</Text>
        </LearningCard>
      )}

      <SectionTitle>همه موضوعات</SectionTitle>
      {statistics.topics.map((topic) => (
          <LearningCard key={topic.id} tone="blue">
          <View style={styles.topicTop}>
            <Text style={styles.topicTitle}>{topic.topic_label}</Text>
            <Text style={styles.topicPercent}>{topic.accuracy_percent}%</Text>
          </View>
          <ProgressBar value={topic.accuracy_percent} />
          <Text style={styles.topicMeta}>
            {topic.questions_answered} پاسخ · {masteryLabel(topic.mastery_state)}
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
