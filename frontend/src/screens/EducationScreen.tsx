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

const PATHS: { tab: string; icon: IconName; labelKey: StringKey }[] = [
  { tab: "quiz", icon: "checklist", labelKey: "quizLabel" },
  { tab: "flashcards", icon: "mobileBlister", labelKey: "cardsLabel" },
  { tab: "lessons", icon: "openBook", labelKey: "lessonsLabel" },
  { tab: "mistakes", icon: "pillWarning", labelKey: "mistakesLabel" },
  { tab: "profile", icon: "team", labelKey: "profileLabel" },
  { tab: "statistics", icon: "chartGrowth", labelKey: "statsLabel" },
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
      <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
        {PATHS.map((p) => (
          <Pressable
            key={p.tab}
            onPress={() => setTab(p.tab as any)}
            style={[
              {
                width: "31.6%",
                backgroundColor: colors.softBg,
                borderRadius: 16,
                alignItems: "center",
                paddingVertical: 12,
              },
              shadows.raisedSm,
            ]}
          >
            <IconImage name={p.icon} size={40} />
            <AppText weight="800" size={12} style={{ marginTop: 2 }}>
              {t(p.labelKey)}
            </AppText>
          </Pressable>
        ))}
      </View>
    </Screen>
  );
}
