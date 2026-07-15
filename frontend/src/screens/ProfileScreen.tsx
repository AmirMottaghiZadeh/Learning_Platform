import React, {useMemo, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {
  BookOpenCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock3,
  LogOut,
  Server,
  ShieldCheck,
  UserRound,
} from "lucide-react-native";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";

import {API_BASE_URL} from "../api/client";
import {platformApi} from "../api/platform";
import {ErrorState, LearningCard, LoadingState, PrimaryButton, ScreenContainer, ScreenHeader, SecondaryButton} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {QuizHistorySession, QuizReminder} from "../types/api";

function formatDateTime(value: string | null) {
  if (!value) return "نامشخص";
  const date = new Date(value);
  return `${date.toLocaleDateString("fa-IR")} · ${date.toLocaleTimeString("fa-IR", {hour: "2-digit", minute: "2-digit"})}`;
}

function formatMode(value: string) {
  if (value === "category") return "دسته‌بندی‌شده";
  if (value === "league") return "لیگ";
  if (value === "mistakes") return "اشتباهات";
  return "تصادفی";
}

export function ProfileScreen() {
  const {user, signOut, token} = useAuth();
  const queryClient = useQueryClient();
  const [expandedReminderId, setExpandedReminderId] = useState<number | null>(null);
  const [expandedSessionId, setExpandedSessionId] = useState<number | null>(null);

  const remindersQuery = useQuery({
    queryKey: ["quiz-reminders", token],
    queryFn: () => platformApi.quizReminders(token!),
    enabled: Boolean(token),
  });
  const historyQuery = useQuery({
    queryKey: ["quiz-history", token],
    queryFn: () => platformApi.quizHistory(token!),
    enabled: Boolean(token),
  });

  const reminderMutation = useMutation({
    mutationFn: ({reminderId, isReviewed}: {reminderId: number; isReviewed: boolean}) =>
      platformApi.updateQuizReminder(token!, reminderId, isReviewed),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ["quiz-reminders"]});
      queryClient.invalidateQueries({queryKey: ["dashboard"]});
      queryClient.invalidateQueries({queryKey: ["statistics"]});
    },
  });

  const reminderStats = useMemo(() => {
    const reminders = remindersQuery.data ?? [];
    return {
      total: reminders.length,
      pending: reminders.filter((item) => !item.is_reviewed).length,
    };
  }, [remindersQuery.data]);

  return (
    <ScreenContainer>
      <ScreenHeader eyebrow="حساب کاربری" title="پروفایل" />
      <LearningCard tone="mint">
        <UserRound size={28} color={colors.primary} />
        <Text style={styles.name}>{user?.username}</Text>
        <Text style={styles.meta}>{user?.email || "ایمیل ثبت نشده است"}</Text>
      </LearningCard>
      <LearningCard tone="amber">
        <View style={styles.row}>
          <ShieldCheck size={24} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.label}>وضعیت دسترسی</Text>
            <Text style={styles.meta}>مسیر یادگیری فعال است.</Text>
          </View>
        </View>
      </LearningCard>
      <LearningCard tone="sage">
        <View style={styles.row}>
          <BookOpenCheck size={24} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.label}>چرخه یادگیری</Text>
            <Text style={styles.meta}>آزمون → اشتباهات → فلش‌کارت → آمار → مرور</Text>
          </View>
        </View>
      </LearningCard>

      {remindersQuery.isLoading ? <LoadingState label="در حال بارگذاری یادآوری‌ها" /> : null}
      {remindersQuery.error ? (
        <ErrorState
          message={remindersQuery.error instanceof Error ? remindersQuery.error.message : "بارگذاری یادآوری‌ها ممکن نیست."}
          onRetry={() => remindersQuery.refetch()}
        />
      ) : null}
      {!remindersQuery.isLoading && !remindersQuery.error ? (
        <>
          <LearningCard tone="lavender">
            <View style={styles.row}>
              <Clock3 size={24} color={colors.primary} />
              <View style={styles.rowText}>
                <Text style={styles.label}>یادآوری‌ها</Text>
                <Text style={styles.meta}>
                  {reminderStats.pending} مورد باز از {reminderStats.total} مورد
                </Text>
              </View>
            </View>
          </LearningCard>
          {(remindersQuery.data ?? []).map((reminder: QuizReminder) => {
            const expanded = expandedReminderId === reminder.id;
            return (
              <LearningCard key={reminder.id} tone={reminder.is_reviewed ? "sage" : "lavender"}>
                <Pressable
                  accessibilityRole="button"
                  onPress={() => setExpandedReminderId(expanded ? null : reminder.id)}
                  style={styles.expandHeader}
                >
                  <View style={styles.expandText}>
                    <Text style={styles.label}>{reminder.question_type_label}</Text>
                    <Text style={styles.meta}>{formatDateTime(reminder.created_at)}</Text>
                  </View>
                  {expanded ? <ChevronUp size={18} color={colors.primary} /> : <ChevronDown size={18} color={colors.primary} />}
                </Pressable>
                <Text style={styles.promptText}>{reminder.prompt}</Text>
                <Text style={styles.meta}>
                  پاسخ درست: {reminder.correct_answer}
                  {reminder.selected_answer ? ` · پاسخ شما: ${reminder.selected_answer}` : ""}
                </Text>
                {expanded ? (
                  <>
                    {reminder.options.length ? <Text style={styles.meta}>گزینه‌ها: {reminder.options.join(" · ")}</Text> : null}
                    {reminder.explanation ? <Text style={styles.meta}>{reminder.explanation}</Text> : null}
                    <View style={styles.actionRow}>
                      <SecondaryButton
                        label={reminder.is_reviewed ? "بازگرداندن به مرور" : "علامت‌گذاری به‌عنوان مرورشده"}
                        Icon={CheckCircle2}
                        onPress={() =>
                          reminderMutation.mutate({reminderId: reminder.id, isReviewed: !reminder.is_reviewed})
                        }
                        disabled={reminderMutation.isPending}
                      />
                    </View>
                  </>
                ) : null}
              </LearningCard>
            );
          })}
        </>
      ) : null}

      {historyQuery.isLoading ? <LoadingState label="در حال بارگذاری لاگ آزمون‌ها" /> : null}
      {historyQuery.data?.length ? (
        historyQuery.data.map((session: QuizHistorySession) => {
          const expanded = expandedSessionId === session.id;
          return (
            <LearningCard key={session.id} tone="blue">
              <Pressable
                accessibilityRole="button"
                onPress={() => setExpandedSessionId(expanded ? null : session.id)}
                style={styles.expandHeader}
              >
                <View style={styles.expandText}>
                  <Text style={styles.label}>{session.question_type_label}</Text>
                  <Text style={styles.meta}>{formatDateTime(session.finished_at ?? session.started_at)}</Text>
                </View>
                {expanded ? <ChevronUp size={18} color={colors.primary} /> : <ChevronDown size={18} color={colors.primary} />}
              </Pressable>
              <Text style={styles.meta}>
                {session.correct_count} صحیح · {session.wrong_count} غلط · {session.total_questions} سؤال
              </Text>
              <Text style={styles.meta}>
                دقت: {session.accuracy_percent}% · امتیاز: {session.score} · مدت: {session.duration_seconds} ثانیه
              </Text>
              <Text style={styles.meta}>حالت: {formatMode(session.mode)}</Text>
              {expanded ? (
                <>
                  <Text style={styles.meta}>پاسخ‌داده‌شده: {session.answered_questions}</Text>
                  <Text style={styles.meta}>زمان هر سؤال: {session.timer_seconds} ثانیه</Text>
                  <Text style={styles.meta}>زمان توقف: {session.total_paused_seconds} ثانیه</Text>
                  {session.answers.map((answer) => (
                    <View key={answer.id} style={styles.answerRow}>
                      <Text style={styles.answerPrompt}>{answer.prompt}</Text>
                      <Text style={[styles.answerMeta, answer.is_correct ? styles.correctText : styles.wrongText]}>
                        {answer.is_correct ? "درست" : "نادرست"} · پاسخ شما: {answer.selected_answer || "بدون پاسخ"}
                      </Text>
                      <Text style={styles.answerMeta}>پاسخ صحیح: {answer.correct_answer}</Text>
                      {answer.options.length ? <Text style={styles.answerMeta}>گزینه‌ها: {answer.options.join(" · ")}</Text> : null}
                      {answer.explanation ? <Text style={styles.answerMeta}>{answer.explanation}</Text> : null}
                    </View>
                  ))}
                </>
              ) : null}
            </LearningCard>
          );
        })
      ) : (
        <LearningCard tone="blue">
          <Text style={styles.label}>لاگ آزمون‌ها</Text>
          <Text style={styles.meta}>هنوز آزمون کاملی ثبت نشده است.</Text>
        </LearningCard>
      )}

      <View style={styles.spacer} />
      <LearningCard tone="blue">
        <Server size={24} color={colors.primary} />
        <Text style={styles.label}>نشانی سرور</Text>
        <Text style={styles.meta}>{API_BASE_URL}</Text>
      </LearningCard>
      <PrimaryButton label="خروج" Icon={LogOut} onPress={signOut} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  name: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  label: {
    color: colors.ink,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  meta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
    lineHeight: 20,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  rowText: {
    flex: 1,
    marginLeft: spacing.md,
  },
  spacer: {
    height: spacing.sm,
  },
  expandHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  expandText: {
    flex: 1,
  },
  promptText: {
    color: colors.ink,
    fontWeight: "900",
    lineHeight: 24,
    marginTop: spacing.sm,
  },
  actionRow: {
    marginTop: spacing.md,
  },
  answerRow: {
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  answerPrompt: {
    color: colors.ink,
    fontWeight: "900",
    lineHeight: 22,
  },
  answerMeta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
    lineHeight: 20,
  },
  correctText: {
    color: colors.success,
  },
  wrongText: {
    color: colors.danger,
  },
});
