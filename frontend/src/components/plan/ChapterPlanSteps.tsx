import { useQuery } from "@tanstack/react-query";
import React from "react";

import { meApi } from "@/api/endpoints";
import type { Chapter } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { spacing } from "@/theme/tokens";
import { formatDay } from "@/utils/planDates";

export function ChapterPlanSteps({ chapter }: { chapter: Chapter }) {
  const { isFa, n, t } = useLang();
  const navigate = useNav((s) => s.navigate);
  const plan = useQuery({
    queryKey: ["plan-chapter", chapter.code],
    queryFn: () => meApi.planChapter(chapter.code),
    retry: false,
  });
  const read = new Set(chapter.progress.read_drug_slugs);
  const hasFinishedReading = chapter.drugs.length > 0 && chapter.drugs.every((drug) => read.has(drug.slug));
  const steps = plan.data;
  const quizDay = steps?.quiz_day ? formatDay(steps.quiz_day, isFa, n) : "";

  return <Card testID="study-chapter-steps" style={{ gap: spacing.sm, marginBottom: spacing.md }}>
    <AppText accessibilityRole="header" weight="800">{isFa ? "برنامهٔ این فصل" : "This chapter’s study plan"}</AppText>
    <AppText size={13}>{n(1)}. {t("lessonsLabel")} · {isFa ? "درس‌های همین فصل را بخوانید." : "Read the lessons in this chapter."}</AppText>
    <AppText size={13} weight="700">{n(2)}. {t("quizLabel")}{quizDay ? ` · ${quizDay}` : ""}</AppText>
    {plan.isError ? <Button full={false} variant="secondary" label={t("retry")} onPress={() => void plan.refetch()} />
      : steps?.quiz_status === "done" ? <AppText muted size={12}>{isFa ? "آزمون انجام شده است." : "Quiz completed"}</AppText>
        : steps?.quiz_status === "unavailable" ? <AppText muted size={12}>{isFa ? "آزمونی برای این فصل در برنامه نیست." : "No quiz is scheduled for this chapter."}</AppText>
          : steps?.quiz_status === "scheduled" && hasFinishedReading
            ? <Button full={false} label={isFa ? "شروع آزمون همین فصل" : "Start chapter quiz"} onPress={() =>
              navigate("quiz", { planChapter: chapter.code, planTitle: isFa ? chapter.name_fa : chapter.name_en })} />
            : <AppText muted size={12}>{isFa ? "بعد از مطالعهٔ دارونامهٔ همین فصل." : "After reading this chapter in Drugbank."}</AppText>}
    {steps?.flashcard_status === "coming_soon" && steps.flashcard_after === "quiz" ? (
      <AppText size={13} testID="study-chapter-flashcards">{n(3)}. {t("tileFlashcards")} · {t("comingSoon")} · {isFa ? "مرور بعد از آزمون همین فصل" : "Review after this chapter’s quiz"}</AppText>
    ) : null}
  </Card>;
}
