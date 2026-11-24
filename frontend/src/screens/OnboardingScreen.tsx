import React from "react";

import { authApi } from "@/api/endpoints";
import type { AtcPlanActivity, AtcPlanConfig } from "@/api/types";
import { AppShell } from "@/components/AppShell";
import { LearningPlanWizard } from "@/components/plan/LearningPlanWizard";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";

export function OnboardingScreen() {
  const { lang } = useLang();
  const setUser = useAuth((state) => state.setUser);
  const finish = async (learning_plan: AtcPlanConfig | null, first?: AtcPlanActivity | null) => {
    const user = await authApi.onboarding({ language: lang, learning_plan });
    if (learning_plan) {
      useNav.getState().reset("dashboard");
      const nav = useNav.getState();
      nav.navigate("planning", { firstActivity: first });
      if (first?.activity_type === "lesson") nav.navigate("lessonList", { code: first.atc_code, studyPlan: true });
    } else useNav.getState().reset("dashboard");
    setUser(user);
  };

  return <AppShell>
    <LearningPlanWizard onClose={() => finish(null)} onSave={finish} />
  </AppShell>;
}
