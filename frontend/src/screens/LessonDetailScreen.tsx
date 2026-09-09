import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { ScreenHeader } from "@/components/ScreenHeader";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function LessonDetailScreen() {
  const { t, isFa } = useLang();
  const { colors } = useTheme();
  const code = String(useNav((s) => s.params.code ?? ""));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["chapter", code],
    queryFn: () => lessonsApi.chapter(code),
    enabled: !!code,
  });

  if (isLoading) return <LoadingState />;

  if (isError || !data) {
    return (
      <Screen>
        <ScreenHeader title={code} back />
        <Card>
          <AppText weight="700" color={colors.denyLabel}>
            {t("emptyDrugsTitle")}
          </AppText>
          <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
            {t("emptyDrugsSub")}
          </AppText>
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      <ScreenHeader
        title={isFa ? data.name_fa : data.name_en}
        subtitle={isFa ? data.group_name_fa : data.group_name_en}
        back
      />
      {data.drugs.map((drug) => {
        const preview = drug.lesson_sections[0];
        return (
          <Card key={drug.slug} style={{ marginBottom: spacing.sm }}>
            <AppText weight="800" size={15}>
              {drug.name}
            </AppText>
            {drug.pharm_classes.length ? (
              <AppText muted weight="600" size={12} style={{ marginTop: 2 }}>
                {drug.pharm_classes.join(" · ")}
              </AppText>
            ) : null}
            {preview ? (
              <View style={{ marginTop: 10 }}>
                <AppText weight="700" size={12} color={colors.accent}>
                  {isFa ? preview.title_fa : preview.title_en}
                </AppText>
                <AppText size={13} style={{ marginTop: 4 }} numberOfLines={4}>
                  {isFa ? preview.text_fa : preview.text_en}
                </AppText>
              </View>
            ) : null}
          </Card>
        );
      })}
    </Screen>
  );
}
