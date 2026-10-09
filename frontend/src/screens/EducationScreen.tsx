import React from "react";
import { Pressable, View } from "react-native";

import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { StringKey } from "@/i18n/strings";

// Lessons leads the list so it lands on the leading edge of the row --
// right in fa (the row is row-reverse there, so the first child sits on the
// right, same mechanism BottomNav uses), left in en -- with the rest
// following in the order a learner actually moves through them: study the
// lesson, test with a quiz, review with flashcards, then check progress.
const PATHS: { tab: string; icon: IconName; labelKey: StringKey }[] = [
  { tab: "lessons", icon: "edu-lessons", labelKey: "lessonsLabel" },
  { tab: "quiz", icon: "edu-quiz", labelKey: "quizLabel" },
  { tab: "flashcards", icon: "edu-flashcards", labelKey: "cardsLabel" },
  { tab: "statistics", icon: "edu-stats", labelKey: "statsLabel" },
  { tab: "mistakes", icon: "edu-mistakes", labelKey: "mistakesLabel" },
  { tab: "profile", icon: "edu-profile", labelKey: "profileLabel" },
];

/** Hub screen for everything that used to sit directly on the dashboard as
 * its own quick-access tile (quiz, flashcards, lessons, mistakes, profile,
 * stats) -- now grouped behind one "Education" entry so the dashboard has
 * room for the Medscape reference sections next to it. */
export function EducationScreen() {
  const { t, row } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const setTab = useNav((s) => s.setTab);

  return (
    <Screen>
      <ScreenChrome title={t("educationLabel")} onBack={goBack} />
      <View style={{ flexDirection: row, flexWrap: "wrap", gap: 12 }}>
        {PATHS.map((p) => (
          <Pressable
            key={p.tab}
            onPress={() => setTab(p.tab as any)}
            style={[
              {
                width: "48%",
                backgroundColor: colors.softBg,
                borderRadius: 18,
                alignItems: "center",
                justifyContent: "center",
                paddingVertical: 26,
                gap: 6,
              },
              shadows.raisedSm,
            ]}
          >
            <IconImage name={p.icon} size={48} />
            <AppText weight="800" size={13.5}>
              {t(p.labelKey)}
            </AppText>
          </Pressable>
        ))}
      </View>
    </Screen>
  );
}
