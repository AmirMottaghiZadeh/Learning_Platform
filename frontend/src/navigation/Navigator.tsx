import React from "react";
import { View } from "react-native";

import { AppShell } from "@/components/AppShell";
import { BottomNav } from "@/components/BottomNav";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { AuthScreen } from "@/screens/AuthScreen";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { LessonDetailScreen } from "@/screens/LessonDetailScreen";
import { LessonsScreen } from "@/screens/LessonsScreen";
import { LockedScreen } from "@/screens/LockedScreen";
import { OnboardingScreen } from "@/screens/OnboardingScreen";
import { ProfileScreen } from "@/screens/ProfileScreen";
import { StubScreen } from "@/screens/StubScreen";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";

export function Navigator() {
  const status = useAuth((s) => s.status);
  const user = useAuth((s) => s.user);

  if (status === "loading") return <LoadingState />;
  if (status === "signedOut") return <AuthScreen />;
  if (user && !user.profile.is_onboarded) return <OnboardingScreen />;

  return (
    <AppShell>
      <View style={{ flex: 1 }}>
        <CurrentScreen />
        <BottomNav />
      </View>
    </AppShell>
  );
}

function CurrentScreen() {
  const screen = useNav((s) => s.screen);
  const { t } = useLang();

  switch (screen) {
    case "lessons":
      return <LessonsScreen />;
    case "lessonDetail":
      return <LessonDetailScreen />;
    case "flashcards":
      return <LockedScreen title={t("cardsTitle")} icon="mobileBlister" />;
    case "quiz":
      return <LockedScreen title={t("quizTitle")} icon="checklist" />;
    case "profile":
      return <ProfileScreen />;
    case "mistakes":
      return <StubScreen title={t("mistakesTitle")} back />;
    case "statistics":
      return <StubScreen title={t("statsTitle")} back />;
    case "planning":
      return <StubScreen title={t("planningTitle")} back />;
    case "uptodate":
      return <StubScreen title={t("uptodateScreenTitle")} subtitle={t("uptodateSourceNote")} back />;
    case "dashboard":
    default:
      return <DashboardScreen />;
  }
}
