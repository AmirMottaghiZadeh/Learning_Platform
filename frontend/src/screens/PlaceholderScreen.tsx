import React from "react";
import { View } from "react-native";

import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { ScreenKey } from "@/navigation/types";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

const META: Partial<Record<ScreenKey, { titleKey: StringKey; icon: IconName }>> = {
  guidelines: { titleKey: "guidelinesLabel", icon: "checklist" },
  diseasesConditions: { titleKey: "diseasesConditionsLabel", icon: "bulbBrain" },
};

/** A section whose UI exists but whose data hasn't been imported yet
 * (the Medscape reference sections, before their databases are loaded). */
export function PlaceholderScreen() {
  const { t } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const screen = useNav((s) => s.screen);
  const meta = META[screen] ?? META.guidelines!;

  return (
    <Screen>
      <ScreenChrome title={t(meta.titleKey)} onBack={goBack} />
      <Card style={{ alignItems: "center", paddingVertical: 32 }}>
        <View
          style={{
            width: 60,
            height: 60,
            borderRadius: 18,
            backgroundColor: colors.softBg,
            borderWidth: 1,
            borderColor: colors.trackBg,
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 14,
          }}
        >
          <IconImage name={meta.icon} size={32} />
        </View>
        <AppText weight="800" size={15} color={colors.accent}>
          {t("comingSoon")}
        </AppText>
        <AppText muted weight="600" size={13} center style={{ marginTop: 6 }}>
          {t("lockedFeature")}
        </AppText>
      </Card>
    </Screen>
  );
}
