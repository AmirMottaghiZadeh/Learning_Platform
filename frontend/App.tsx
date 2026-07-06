import React, {useState} from "react";
import {SafeAreaProvider} from "react-native-safe-area-context";

import {AppShell} from "./src/components/AppShell";
import {LoadingState} from "./src/components/ui";
import type {ScreenKey} from "./src/navigation/types";
import {AuthScreen} from "./src/screens/AuthScreen";
import {DashboardScreen} from "./src/screens/DashboardScreen";
import {FlashcardsScreen} from "./src/screens/FlashcardsScreen";
import {LeagueScreen} from "./src/screens/LeagueScreen";
import {MistakesScreen} from "./src/screens/MistakesScreen";
import {ProfileScreen} from "./src/screens/ProfileScreen";
import {QuizScreen} from "./src/screens/QuizScreen";
import {StatisticsScreen} from "./src/screens/StatisticsScreen";
import {AuthProvider, useAuth} from "./src/store/auth";
import {configureAppFonts} from "./src/design/fonts";

configureAppFonts();

function MainApp() {
  const {token, loading} = useAuth();
  const [screen, setScreen] = useState<ScreenKey>("dashboard");

  if (loading) return <LoadingState label="Loading session" />;
  if (!token) return <AuthScreen />;

  return (
    <AppShell active={screen} onNavigate={setScreen}>
      {screen === "dashboard" ? <DashboardScreen onNavigate={setScreen} /> : null}
      {screen === "quiz" ? <QuizScreen /> : null}
      {screen === "flashcards" ? <FlashcardsScreen /> : null}
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
        <MainApp />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
