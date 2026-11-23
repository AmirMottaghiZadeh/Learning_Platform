import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";

import { meApi } from "@/api/endpoints";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export const PLAN_BRIEF_KEY = ["plan-today-brief"];

export function PlanSection() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);
  const { data: plan } = useQuery({ queryKey: ["plan"], queryFn: meApi.plan, retry: false });
  const { data } = useQuery({
    queryKey: PLAN_BRIEF_KEY, queryFn: meApi.planTodayBrief,
    enabled: plan?.mode === "goal", retry: false, refetchOnMount: "always",
  });
  const next = data?.items.find((item) => item.status === "pending");
  const done = data?.items.filter((item) => item.status === "done").length ?? 0;
  const total = data?.items.length ?? 0;
  const hasPlan = plan?.mode === "goal";
  return (
    <View style={{ gap: spacing.sm }}>
      <AppText accessibilityRole="header" aria-level={2} size={18} weight="800">{t("planSectionTitle")}</AppText>
      <Card style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: row, alignItems: "baseline", justifyContent: "space-between", gap: spacing.xs }}>
          <AppText weight="800" size={15} style={{ flex: 1 }}>{isFa ? "مسیر مطالعهٔ داروها" : "Drug study pathway"}</AppText>
          {total > 0 ? <AppText size={12} weight="700" color={colors.accent}>{n(done)}/{n(total)}</AppText> : null}
        </View>
        <AppText size={13} muted>{next ? (isFa ? next.title_fa : next.title_en) : (isFa ? "دارونامه، آزمون و فلش‌کارت (به‌زودی)" : "Drugbank, quizzes and flashcards (coming soon)")}</AppText>
        <Button full={false} label={hasPlan ? (isFa ? "باز کردن برنامه" : "Open study plan") : t("planningCreateCta")}
          onPress={() => navigate(plan && !hasPlan ? "planningSetup" : "planning")}
          style={{ minHeight: 44, marginTop: 2 }} />
      </Card>
    </View>
  );
}
