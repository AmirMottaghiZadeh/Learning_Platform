import React from "react";
import { View } from "react-native";

import { CLINICAL_TILES, HomeTileGrid } from "@/components/HomeTileGrid";
import { ScreenChrome } from "@/components/ScreenChrome";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";

export function ClinicalScreen() {
  const { t } = useLang();
  const goBack = useNav((state) => state.goBack);
  const canGoBack = useNav((state) => state.history.length > 0);

  return (
    <Screen animateEntrance={false} contentStyle={{ maxWidth: 780 }}>
      <ScreenChrome title={t("clinicalResources")} onBack={canGoBack ? goBack : undefined} />
      <View testID="clinical-paths">
        <HomeTileGrid rows={[CLINICAL_TILES.slice(0, 3), CLINICAL_TILES.slice(3)]} />
      </View>
    </Screen>
  );
}
