import React from "react";
import { View } from "react-native";

import { ScreenHeader } from "@/components/ScreenHeader";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export function LockedScreen({ title, icon }: { title: string; icon: IconName }) {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <Screen>
      <ScreenHeader title={title} />
      <Card>
        <View style={{ alignItems: "center", gap: 12, paddingVertical: 24 }}>
          <View
            style={{
              width: 60,
              height: 60,
              borderRadius: 18,
              backgroundColor: colors.softBg,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <IconImage name={icon} size={34} />
          </View>
          <AppText weight="800" size={15}>
            {t("comingSoon")}
          </AppText>
          <AppText muted weight="600" size={13} center>
            {t("lockedFeature")}
          </AppText>
        </View>
      </Card>
    </Screen>
  );
}
