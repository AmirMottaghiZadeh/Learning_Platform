import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, ScrollView, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

export function LessonListScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const code = String(useNav((s) => s.params.code ?? ""));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["chapter", code],
    queryFn: () => lessonsApi.chapter(code),
    enabled: !!code,
  });

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ paddingHorizontal: 22, paddingTop: 18 }}>
        <ChromeButton onPress={goBack} size={30}>
          <AppText weight="800" size={15} color={colors.ink}>
            {isFa ? "›" : "‹"}
          </AppText>
        </ChromeButton>

        {isLoading ? null : isError || !data ? (
          <>
            <AppText weight="900" size={22} style={{ marginTop: 16 }}>
              {t("emptyDrugsTitle")}
            </AppText>
            <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
              {t("emptyDrugsSub")}
            </AppText>
          </>
        ) : (
          <>
            <AppText
              weight="900"
              size={10}
              color={colors.accent}
              style={{ marginTop: 16, letterSpacing: 1.4 }}
            >
              {(isFa ? data.group_name_fa : data.group_name_en).toUpperCase()}
            </AppText>
            <AppText weight="900" size={24} style={{ marginTop: 6, lineHeight: 34 }}>
              {isFa ? data.name_fa : data.name_en}
            </AppText>
            <AppText weight="700" size={12.5} muted style={{ marginTop: 5 }}>
              {data.code} · {isFa ? data.anatomical_name_fa : data.anatomical_name_en} ·{" "}
              {n(data.drugs.length)} {t("lessonsUnit")}
            </AppText>
            {data.topics.length > 1 ? (
              <AppText weight="600" size={11.5} color={colors.accent} style={{ marginTop: 6 }}>
                {t("alsoRelevantTo")}:{" "}
                {data.topics
                  .slice(1)
                  .map((topic) => (isFa ? topic.name_fa : topic.name_en))
                  .join(isFa ? "، " : ", ")}
              </AppText>
            ) : null}
          </>
        )}
        <View style={{ height: 1, backgroundColor: colors.sheetLine, marginTop: 16 }} />
      </View>

      {isLoading ? (
        <LoadingState />
      ) : (
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 22, paddingBottom: 40, gap: 10 }}
          showsVerticalScrollIndicator={false}
        >
          {(data?.drugs ?? []).map((drug, i) => {
            const done = data?.progress.read_drug_slugs.includes(drug.slug);
            return (
              <Pressable
                key={drug.slug}
                onPress={() => navigate("lessonDetail", { code, slug: drug.slug })}
                style={{
                  flexDirection: row,
                  alignItems: "center",
                  gap: 12,
                  backgroundColor: colors.softBg,
                  borderRadius: 14,
                  padding: 14,
                }}
              >
                <View
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 9,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: done ? colors.accent : colors.cardBg,
                    borderWidth: 1,
                    borderColor: colors.trackBg,
                  }}
                >
                  <AppText weight="800" size={12} color={done ? colors.onAccent : colors.muted}>
                    {done ? "✓" : n(i + 1)}
                  </AppText>
                </View>
                <View style={{ flex: 1 }}>
                  <AppText weight="800" size={14}>
                    {drug.name}
                  </AppText>
                  {drug.pharm_classes.length ? (
                    <AppText muted weight="600" size={12} numberOfLines={1} style={{ marginTop: 2 }}>
                      {drug.pharm_classes.join(" · ")}
                    </AppText>
                  ) : null}
                </View>
                <AppText muted size={13}>
                  {isFa ? "‹" : "›"}
                </AppText>
              </Pressable>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}
