import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";

import { meApi } from "@/api/endpoints";
import { useStudyTrack } from "@/components/plan/ClinicalPlan";
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
  const { track, tasks } = useStudyTrack();
  const { data } = useQuery({
    queryKey: PLAN_BRIEF_KEY, queryFn: meApi.planTodayBrief,
    enabled: track === "student", retry: false, refetchOnMount: "always",
  });
  const next = data?.items.find((item) => item.status === "pending");
  const done = data?.items.filter((item) => item.status === "done").length ?? 0;
  const total = data?.items.length ?? 0;
  const clinical = track === "clinical";
  const topics = Object.values(tasks).filter((task) => task?.topic).length;
  return (
    <View style={{ gap: spacing.sm }}>
      <AppText accessibilityRole="header" aria-level={2} size={18} weight="800">{t("planSectionTitle")}</AppText>
      <Card style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: row, alignItems: "baseline", justifyContent: "space-between", gap: spacing.xs }}>
          <AppText weight="800" size={15} style={{ flex: 1 }}>{clinical
            ? (isFa ? "مرور بالینی" : "Clinical reading")
            : (isFa ? "مسیر دانشجوی داروسازی" : "Pharmacy student pathway")}</AppText>
          {total > 0 && !clinical ? <AppText size={12} weight="700" color={colors.accent}>{n(done)}/{n(total)}</AppText> : null}
        </View>
        <AppText size={13} muted>{clinical
          ? (topics ? (isFa ? `${n(topics)} موضوع در برنامهٔ مرور` : `${topics} topics on your reading plan`) : (isFa ? "موضوع مطالعه را برای هر مرجع انتخاب کنید." : "Choose a reading topic for each reference."))
          : next ? (isFa ? next.title_fa : next.title_en) : (isFa ? "دارونامه، آزمون و مرور با فلش‌کارت" : "Formulary, quiz and flashcard review")}</AppText>
        <Button full={false} label={isFa ? "باز کردن برنامه" : "Open study plan"} onPress={() => navigate("planning")}
          style={{ minHeight: 44, marginTop: 2 }} />
      </Card>
    </View>
  );
}
