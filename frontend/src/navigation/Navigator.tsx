import React, { useEffect, useRef } from "react";
import { AiLabScreen } from "@/screens/AiLabScreen";
import { SupportScreen } from "@/screens/SupportScreen";
import { DevicesScreen } from "@/screens/DevicesScreen";
import { BackHandler, Platform, ToastAndroid, View } from "react-native";

import { AppShell } from "@/components/AppShell";
import { BottomNav } from "@/components/BottomNav";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { AuthScreen } from "@/screens/AuthScreen";
import { PediatricDoseScreen } from "@/screens/PediatricDoseScreen";
import { PEDIATRIC_DOSE_SLUG } from "@/pediatricDose/catalog";
import { CalculatorDetailScreen } from "@/screens/CalculatorDetailScreen";
import { CalculatorDomainScreen } from "@/screens/CalculatorDomainScreen";
import { CalculatorsScreen } from "@/screens/CalculatorsScreen";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { EducationScreen } from "@/screens/EducationScreen";
import { ClinicalScreen } from "@/screens/ClinicalScreen";
import { ResourceLookup } from "@/components/ResourceLookup";
import { ScreenChrome } from "@/components/ScreenChrome";
import { Screen } from "@/components/primitives/Screen";
import { LessonDetailScreen } from "@/screens/LessonDetailScreen";
import { LessonListScreen } from "@/screens/LessonListScreen";
import { LessonsScreen } from "@/screens/LessonsScreen";
import { DownloadsScreen } from "@/screens/DownloadsScreen";
import { SettingsScreen } from "@/screens/SettingsScreen";
import { PlansScreen } from "@/screens/PlansScreen";
import { LexicompScreen } from "@/screens/LexicompScreen";
import { MedscapeArticleScreen } from "@/screens/MedscapeArticleScreen";
import { MedscapeBrowseScreen } from "@/screens/MedscapeBrowseScreen";
import { MedscapeGuidelinesScreen } from "@/screens/MedscapeGuidelinesScreen";
import { MedscapeOutlineScreen } from "@/screens/MedscapeOutlineScreen";
import { MedscapeSpecialtyScreen } from "@/screens/MedscapeSpecialtyScreen";
import { MistakesScreen } from "@/screens/MistakesScreen";
import { OnboardingScreen } from "@/screens/OnboardingScreen";
import { PlanningScreen } from "@/screens/PlanningScreen";
import { PlanningSetupScreen } from "@/screens/PlanningSetupScreen";
import { ProfileScreen } from "@/screens/ProfileScreen";
import { QuizScreen } from "@/screens/QuizScreen";
import { SetPasswordScreen } from "@/screens/SetPasswordScreen";
import { StatisticsScreen } from "@/screens/StatisticsScreen";
import { UptodateArticleScreen } from "@/screens/UptodateArticleScreen";
import { UptodateOutlineScreen } from "@/screens/UptodateOutlineScreen";
import { UptodateScreen } from "@/screens/UptodateScreen";
import { useAuth } from "@/store/auth";
import { goBackInApp, installWebBackGuard } from "@/navigation/back";
import { resourceDestination } from "@/navigation/resourceDestination";
import { useNav } from "@/store/nav";

export function Navigator() {
  const status = useAuth((s) => s.status);
  const user = useAuth((s) => s.user);
  const mustSetPassword = useAuth((s) => s.mustSetPassword);

  const openedDestination = useRef(false);
  const needsPassword = Boolean(user && !user.is_guest && (user.has_password === false || mustSetPassword));
  const ready = status === "signedIn" && Boolean(user?.profile.is_onboarded) && !needsPassword;

  useEffect(() => {
    if (Platform.OS !== "web" || !ready || openedDestination.current) return;
    openedDestination.current = true;
    const target = resourceDestination(window.location.search);
    if (!target) return;
    const nav = useNav.getState();
    if (target.screen === nav.screen) nav.setParams(target.params ?? {});
    else nav.navigate(target.screen, target.params);
  }, [ready]);

  let content: React.ReactNode;
  if (status === "loading") content = <LoadingState />;
  else if (status === "signedOut") content = <AuthScreen />;
  // Signed in with an SMS code: a password comes before anything else.
  else if (needsPassword) content = <SetPasswordScreen />;
  else if (user && !user.profile.is_onboarded) content = <OnboardingScreen />;
  else {
    content = (
      <AppShell padBottom={false}>
        <View style={{ flex: 1 }}>
          <View style={{ flex: 1 }}>
            <CurrentScreen />
          </View>
          <BottomNav />
        </View>
      </AppShell>
    );
  }

  return (
    <>
      <AndroidBackButton />
      <WebBackGuard />
      {content}
    </>
  );
}

const EXIT_CONFIRM_MS = 2000;

/** Android's hardware/gesture Back: one step back inside the app (see
 * navigation/back) instead of the OS default of closing the app from any
 * screen. At the app's root it takes a second press within EXIT_CONFIRM_MS to
 * leave, so a stray swipe doesn't. */
function AndroidBackButton() {
  const { t } = useLang();
  const lastPress = useRef(0);

  useEffect(() => {
    if (Platform.OS !== "android") return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      if (goBackInApp()) return true;
      const now = Date.now();
      if (now - lastPress.current < EXIT_CONFIRM_MS) return false; // let the OS close the app
      lastPress.current = now;
      ToastAndroid.show(t("pressBackAgainToExit"), ToastAndroid.SHORT);
      return true;
    });
    return () => sub.remove();
  }, [t]);

  return null;
}

/** The browser's back as an in-app step back -- see installWebBackGuard. */
function WebBackGuard() {
  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") return;
    return installWebBackGuard(window);
  }, []);
  return null;
}

function CurrentScreen() {
  const screen = useNav((s) => s.screen);
  const calculatorSlug = useNav((s) => s.params.slug);

  switch (screen) {
    case "aiLab":
      return <AiLabScreen />;
    case "support":
      return <SupportScreen />;
    case "devices":
      return <DevicesScreen />;
    case "resourceSearch":
      return <ResourceSearchScreen />;
    case "lessons":
      return <LessonsScreen />;
    case "lessonList":
      return <LessonListScreen />;
    case "lessonDetail":
      return <LessonDetailScreen />;
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
    case "planningSetup":
      return <PlanningSetupScreen />;
    case "uptodate":
      return <UptodateScreen />;
    case "uptodateOutline":
      return <UptodateOutlineScreen />;
    case "uptodateArticle":
      return <UptodateArticleScreen />;
    case "lexicomp":
      return <LexicompScreen />;
    case "downloads":
      return <DownloadsScreen />;
    case "settings":
      return <SettingsScreen />;
    case "plans":
      return <PlansScreen />;
    case "education":
      return <EducationScreen />;
    case "clinical":
      return <ClinicalScreen />;
    case "guidelines":
      return <MedscapeGuidelinesScreen />;
    case "diseasesConditions":
      return <MedscapeBrowseScreen />;
    case "medscapeOutline":
      return <MedscapeOutlineScreen />;
    case "medscapeArticle":
      return <MedscapeArticleScreen />;
    case "medscapeSpecialty":
      return <MedscapeSpecialtyScreen />;
    case "calculator":
      return <CalculatorsScreen />;
    case "calculatorDomain":
      return <CalculatorDomainScreen />;
    case "calculatorDetail":
      return calculatorSlug === PEDIATRIC_DOSE_SLUG ? <PediatricDoseScreen /> : <CalculatorDetailScreen />;
    case "dashboard":
    default:
      return <DashboardScreen />;
  }
}

function ResourceSearchScreen() {
  const { t } = useLang();
  const goBack = useNav((state) => state.goBack);
  return (
    <Screen contentStyle={{ maxWidth: 820 }} keyboardShouldPersistTaps="handled">
      <ScreenChrome title={t("resourceLookupTitle")} onBack={goBack} />
      <ResourceLookup />
    </Screen>
  );
}
