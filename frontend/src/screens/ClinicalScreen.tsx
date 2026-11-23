import React from "react";
import { View } from "react-native";

import { CLINICAL_TILES, HomeTileGrid } from "@/components/HomeTileGrid";
import { ScreenChrome } from "@/components/ScreenChrome";
import { SmartSearchHomeCard } from "@/components/SmartSearchHomeCard";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { spacing } from "@/theme/tokens";

export function ClinicalScreen() {
  const { t } = useLang();
  const navigate = useNav((state) => state.navigate);
  const goBack = useNav((state) => state.goBack);
  const canGoBack = useNav((state) => state.history.length > 0);

  return (
    <Screen animateEntrance={false} contentStyle={{ maxWidth: 780 }}>
      <ScreenChrome title={t("clinicalResources")} onBack={canGoBack ? goBack : undefined} />
      <View testID="clinical-paths" style={{ gap: spacing.lg }}>
        <HomeTileGrid title="resourceLookupQuick" rows={[CLINICAL_TILES.slice(0, 3), CLINICAL_TILES.slice(3)]} />
        <SmartSearchHomeCard onPress={() => navigate("aiLab")} />
      </View>
    </Screen>
  );
}
