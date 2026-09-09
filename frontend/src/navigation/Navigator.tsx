import React from "react";
import { View } from "react-native";

import { AppShell } from "@/components/AppShell";
import { BottomNav } from "@/components/BottomNav";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { AuthScreen } from "@/screens/AuthScreen";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { LessonDetailScreen } from "@/screens/LessonDetailScreen";
import { LessonListScreen } from "@/screens/LessonListScreen";
import { LessonsScreen } from "@/screens/LessonsScreen";
import { FlashcardsScreen } from "@/screens/FlashcardsScreen";
import { MistakesScreen } from "@/screens/MistakesScreen";
import { OnboardingScreen } from "@/screens/OnboardingScreen";
import { PlanningScreen } from "@/screens/PlanningScreen";
import { ProfileScreen } from "@/screens/ProfileScreen";
import { QuizScreen } from "@/screens/QuizScreen";
import { StatisticsScreen } from "@/screens/StatisticsScreen";
import { UptodateArticleScreen } from "@/screens/UptodateArticleScreen";
import { UptodateScreen } from "@/screens/UptodateScreen";
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
    case "lessonList":
      return <LessonListScreen />;
    case "lessonDetail":
      return <LessonDetailScreen />;
    case "flashcards":
      return <FlashcardsScreen />;
    case "quiz":
      return <QuizScreen />;
    case "profile":
      return <ProfileScreen />;
    case "mistakes":
      return <MistakesScreen />;
    case "statistics":
      return <StatisticsScreen />;
    case "planning":
      return <PlanningScreen />;
    case "uptodate":
      return <UptodateScreen />;
    case "uptodateArticle":
      return <UptodateArticleScreen />;
    case "dashboard":
    default:
      return <DashboardScreen />;
  }
}
