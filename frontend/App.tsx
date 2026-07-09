import React, {useEffect, useState} from "react";
import {SafeAreaProvider} from "react-native-safe-area-context";

import {AppShell} from "./src/components/AppShell";
import {LoadingState} from "./src/components/ui";
import type {ScreenKey} from "./src/navigation/types";
import {AuthScreen} from "./src/screens/AuthScreen";
import {DashboardScreen} from "./src/screens/DashboardScreen";
import {FlashcardsScreen} from "./src/screens/FlashcardsScreen";
import {LeagueScreen} from "./src/screens/LeagueScreen";
import {MistakesScreen} from "./src/screens/MistakesScreen";
import {PlanningScreen} from "./src/screens/PlanningScreen";
import {ProfileScreen} from "./src/screens/ProfileScreen";
import {QuizScreen} from "./src/screens/QuizScreen";
import {StatisticsScreen} from "./src/screens/StatisticsScreen";
import {AuthProvider, useAuth} from "./src/store/auth";
import {OnboardingProvider, useOnboarding} from "./src/store/onboarding";
import {configureAppFonts} from "./src/design/fonts";
import {OnboardingScreen} from "./src/screens/OnboardingScreen";

configureAppFonts();

function registerServiceWorker() {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => undefined);
  });
}

function MainApp() {
  const {token, loading} = useAuth();
  const {completed, loading: onboardingLoading, completeOnboarding} = useOnboarding();
  const [screen, setScreen] = useState<ScreenKey>("dashboard");

  useEffect(() => {
    registerServiceWorker();
  }, []);

  if (loading || onboardingLoading) return <LoadingState label="Loading session" />;
  if (!token) return <AuthScreen />;
  if (!completed) return <OnboardingScreen onDone={completeOnboarding} />;

  return (
    <AppShell active={screen} onNavigate={setScreen}>
      {screen === "dashboard" ? <DashboardScreen onNavigate={setScreen} /> : null}
      {screen === "quiz" ? <QuizScreen /> : null}
      {screen === "flashcards" ? <FlashcardsScreen /> : null}
      {screen === "planning" ? <PlanningScreen onNavigate={setScreen} /> : null}
      {screen === "mistakes" ? <MistakesScreen /> : null}
      {screen === "league" ? <LeagueScreen /> : null}
      {screen === "statistics" ? <StatisticsScreen /> : null}
      {screen === "profile" ? <ProfileScreen /> : null}
    </AppShell>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <OnboardingProvider>
          <MainApp />
        </OnboardingProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
