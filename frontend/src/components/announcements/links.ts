import { Linking } from "react-native";

import { AnnouncementButton } from "@/api/types";
import { ScreenKey, TabKey } from "@/navigation/types";

type Nav = {
  navigate: (screen: ScreenKey, params?: Record<string, unknown>) => void;
  setTab: (tab: TabKey) => void;
};

// Where an announcement's in-app button goes; the keys are the backend's
// AppAnnouncement.SCREEN_CHOICES.
const SCREENS: Record<string, (nav: Nav, param: string) => void> = {
  lessons: (nav) => nav.setTab("lessons"),
  lesson: (nav, code) => nav.navigate("lessonList", { code }),
  flashcards: (nav) => nav.setTab("flashcards"),
  leitner: (nav) => nav.navigate("flashcards", { leitner: true }),
  quiz: (nav) => nav.setTab("quiz"),
  uptodate: (nav) => nav.navigate("uptodate"),
  lexicomp: (nav) => nav.navigate("lexicomp"),
  calculator: (nav) => nav.navigate("calculator"),
  guidelines: (nav) => nav.navigate("guidelines"),
  diseases: (nav) => nav.navigate("diseasesConditions"),
  planning: (nav) => nav.navigate("planning"),
  statistics: (nav) => nav.navigate("statistics"),
  downloads: (nav) => nav.navigate("downloads"),
  profile: (nav) => nav.setTab("profile"),
};

/** Follow an announcement's button: a web page in the browser, or a part
 * of the app. An unknown screen (a newer backend) does nothing. */
export function openButton(button: AnnouncementButton, nav: Nav) {
  if (button.kind === "url") {
    if (/^https?:\/\//.test(button.url)) Linking.openURL(button.url).catch(() => undefined);
    return;
  }
  SCREENS[button.screen]?.(nav, button.param);
}
