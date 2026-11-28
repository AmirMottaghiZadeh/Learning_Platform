import { useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";

import { meApi } from "@/api/endpoints";
import { useNavClearance } from "@/components/BottomNav";
import { DEFAULT_PLAN, LearningPlanWizard } from "@/components/plan/LearningPlanWizard";
import { PLAN_BRIEF_KEY } from "@/components/plan/PlanSection";
import { Button } from "@/components/primitives/Button";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { ScreenChrome } from "@/components/ScreenChrome";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { daysUntil } from "@/utils/planDates";

export function PlanningSetupScreen() {
  const { t, isFa } = useLang();
  const goBack = useNav((state) => state.goBack);
  const navigate = useNav((state) => state.navigate);
  const clearance = useNavClearance();
  const client = useQueryClient();
  const plan = useQuery({ queryKey: ["plan"], queryFn: meApi.plan, retry: false });

  if (!plan.data) return <Screen animateEntrance={false}>
    <ScreenChrome title={t("planningTitle")} onBack={goBack} />
    {plan.isPending ? <LoadingState /> : <Button label={isFa ? "تلاش دوباره" : "Retry"} onPress={() => void plan.refetch()} />}
  </Screen>;

  const current = plan.data;
  const initial = current.mode === "goal" ? {
    atc_groups: current.atc_groups ?? [],
    daily_minutes: Math.max(15, current.daily_minutes),
    days: current.days.some(Boolean) ? current.days : DEFAULT_PLAN.days,
    deadline: current.deadline && daysUntil(current.deadline) > 0 ? current.deadline : null,
  } : DEFAULT_PLAN;

  return <Screen animateEntrance={false} padded={false} scroll={false}>
    <LearningPlanWizard initial={initial} bottomInset={clearance} isEditing onClose={goBack}
      onSave={async (config, first) => {
        const saved = await meApi.savePlan(config);
        client.setQueryData(["plan"], saved);
        void client.invalidateQueries({ queryKey: ["plan-today"] });
        void client.invalidateQueries({ queryKey: PLAN_BRIEF_KEY });
        void client.invalidateQueries({ queryKey: ["plan-chapter"] });
        goBack();
        if (first?.activity_type === "lesson") navigate("lessonList", { code: first.atc_code, studyPlan: true });
      }}
    />
  </Screen>;
}
