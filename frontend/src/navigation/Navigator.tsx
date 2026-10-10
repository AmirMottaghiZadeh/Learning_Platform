import React, { useEffect, useRef } from "react";
import { Animated, BackHandler, Easing, Platform, ToastAndroid, View } from "react-native";

import { AppShell } from "@/components/AppShell";
import { BottomNav } from "@/components/BottomNav";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { AuthScreen } from "@/screens/AuthScreen";
import { CalculatorDetailScreen } from "@/screens/CalculatorDetailScreen";
import { CalculatorDomainScreen } from "@/screens/CalculatorDomainScreen";
import { CalculatorsScreen } from "@/screens/CalculatorsScreen";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { EducationScreen } from "@/screens/EducationScreen";
import { LessonDetailScreen } from "@/screens/LessonDetailScreen";
import { LessonListScreen } from "@/screens/LessonListScreen";
import { LessonsScreen } from "@/screens/LessonsScreen";
import { LexicompScreen } from "@/screens/LexicompScreen";
import { FlashcardsScreen } from "@/screens/FlashcardsScreen";
import { MedscapeArticleScreen } from "@/screens/MedscapeArticleScreen";
import { MedscapeBrowseScreen } from "@/screens/MedscapeBrowseScreen";
import { MedscapeGuidelinesScreen } from "@/screens/MedscapeGuidelinesScreen";
import { MedscapeSpecialtyScreen } from "@/screens/MedscapeSpecialtyScreen";
import { MistakesScreen } from "@/screens/MistakesScreen";
import { OnboardingScreen } from "@/screens/OnboardingScreen";
import { PlanningScreen } from "@/screens/PlanningScreen";
import { PlanningSetupScreen } from "@/screens/PlanningSetupScreen";
import { ProfileScreen } from "@/screens/ProfileScreen";
import { QuizScreen } from "@/screens/QuizScreen";
import { StatisticsScreen } from "@/screens/StatisticsScreen";
import { UptodateArticleScreen } from "@/screens/UptodateArticleScreen";
import { UptodateOutlineScreen } from "@/screens/UptodateOutlineScreen";
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
      <AndroidBackButton />
      <View style={{ flex: 1 }}>
        <ScreenTransition>
          <CurrentScreen />
        </ScreenTransition>
        <BottomNav />
      </View>
    </AppShell>
  );
}

const EXIT_CONFIRM_MS = 2000;

/** Android's hardware/gesture Back: steps back through the in-app history
 * like a native stack would, instead of the OS default of closing the app
 * from any screen. From another tab's root it returns Home first; on Home it
 * takes a second press within EXIT_CONFIRM_MS to leave the app, so a stray
 * swipe doesn't. Open Modals (help sheet, image viewer) get Back before this
 * via their own onRequestClose. */
function AndroidBackButton() {
  const { t } = useLang();
  const lastPress = useRef(0);

  useEffect(() => {
    if (Platform.OS !== "android") return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      const { screen, history, goBack, setTab } = useNav.getState();
      if (history.length > 0) {
        goBack();
        return true;
      }
      if (screen !== "dashboard") {
        setTab("dashboard");
        return true;
      }
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

const SLIDE_DISTANCE = 28;

/** Replays a short enter animation each time the screen changes: a slide
 * from the trailing edge going deeper, from the leading edge coming back
 * (mirrored for RTL, where "forward" reads right-to-left), and a plain fade
 * for tab switches -- the screen-to-screen motion a native app has, instead
 * of the instant swap that made navigation feel like following web links. */
function ScreenTransition({ children }: { children: React.ReactNode }) {
  const transitionId = useNav((s) => s.transitionId);
  const direction = useNav((s) => s.direction);
  const { isFa } = useLang();
  const progress = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (transitionId === 0) return; // first render: nothing to animate from
    progress.setValue(0);
    Animated.timing(progress, {
      toValue: 1,
      duration: direction === "tab" ? 160 : 240,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: Platform.OS !== "web",
    }).start();
  }, [transitionId, direction, progress]);

  // Physical px the screen starts offset by: positive = starts to the right.
  const fromRight = direction === "forward" ? !isFa : isFa;
  const offset = direction === "tab" ? 0 : fromRight ? SLIDE_DISTANCE : -SLIDE_DISTANCE;

  return (
    <Animated.View
      style={{
        flex: 1,
        opacity: progress,
        transform: [{ translateX: progress.interpolate({ inputRange: [0, 1], outputRange: [offset, 0] }) }],
      }}
    >
      {children}
    </Animated.View>
  );
}

function CurrentScreen() {
  const screen = useNav((s) => s.screen);

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
    case "education":
      return <EducationScreen />;
    case "guidelines":
      return <MedscapeGuidelinesScreen />;
    case "diseasesConditions":
      return <MedscapeBrowseScreen />;
    case "medscapeArticle":
      return <MedscapeArticleScreen />;
    case "medscapeSpecialty":
      return <MedscapeSpecialtyScreen />;
    case "calculator":
      return <CalculatorsScreen />;
    case "calculatorDomain":
      return <CalculatorDomainScreen />;
    case "calculatorDetail":
      return <CalculatorDetailScreen />;
    case "dashboard":
    default:
      return <DashboardScreen />;
  }
}
