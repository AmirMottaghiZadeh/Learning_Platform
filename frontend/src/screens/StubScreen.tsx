import React from "react";
import { View } from "react-native";

import { ScreenHeader } from "@/components/ScreenHeader";
import { Card } from "@/components/primitives/Card";
import { AppText } from "@/components/primitives/AppText";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export function StubScreen({
  title,
  subtitle,
  note,
  back,
}: {
  title: string;
  subtitle?: string;
  note?: string;
  back?: boolean;
}) {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <Screen>
      <ScreenHeader title={title} subtitle={subtitle} back={back} />
      <Card>
        <View style={{ gap: 8 }}>
          <AppText weight="800" size={15} color={colors.accent}>
            {t("comingSoon")}
          </AppText>
          <AppText muted weight="600" size={13}>
            {note ?? t("stubNote")}
          </AppText>
        </View>
      </Card>
    </Screen>
  );
}
