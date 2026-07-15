import React, {useCallback, useEffect, useState} from "react";
import {StyleSheet, Text, View} from "react-native";
import {AlertTriangle, RefreshCw} from "lucide-react-native";

import {platformApi} from "../api/platform";
import {EmptyState, ErrorState, LearningCard, LoadingState, ScreenContainer, ScreenHeader, SecondaryButton} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import type {Mistake} from "../types/api";

export function MistakesScreen() {
  const {token} = useAuth();
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setMistakes(await platformApi.mistakes(token));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "بارگذاری اشتباهات ممکن نیست.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="در حال بارگذاری اشتباهات" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <ScreenContainer>
      <ScreenHeader
        eyebrow={`${mistakes.length} مورد`}
        title="اشتباهات"
        action={<SecondaryButton label="بروزرسانی" Icon={RefreshCw} onPress={load} />}
      />
      {!mistakes.length ? (
        <EmptyState title="اشتباهی ثبت نشده است" />
      ) : (
        mistakes.map((mistake) => (
          <LearningCard key={mistake.id} tone="rose">
            <View style={styles.top}>
              <AlertTriangle size={20} color={colors.rose} />
              <Text style={styles.count}>{mistake.wrong_count} بار</Text>
            </View>
            <Text style={styles.prompt}>{mistake.prompt}</Text>
            <Text style={styles.answer}>{mistake.correct_answer}</Text>
            {mistake.feedback ? <Text style={styles.feedback}>{mistake.feedback}</Text> : null}
          </LearningCard>
        ))
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  top: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  count: {
    color: colors.rose,
    fontWeight: "900",
  },
  prompt: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    lineHeight: 27,
  },
  answer: {
    color: colors.ink,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  feedback: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 20,
    marginTop: spacing.sm,
  },
});
