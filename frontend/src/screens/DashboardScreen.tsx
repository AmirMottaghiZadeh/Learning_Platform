import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { ScreenHeader } from "@/components/ScreenHeader";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function DashboardScreen() {
  const { t, isFa, n } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["dashboard"],
    queryFn: meApi.dashboard,
  });

  if (isLoading) return <LoadingState />;

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenHeader
        title={`${t("greeting")} ${data?.greeting_name ?? ""}`.trim()}
        subtitle={t("greetingSub")}
      />

      {isError ? (
        <Card>
          <AppText weight="700" color={colors.denyLabel}>
            {t("loadFailed")}
          </AppText>
        </Card>
      ) : (
        <>
          <View style={{ flexDirection: "row", gap: spacing.md, marginBottom: spacing.lg }}>
            <Stat label={t("streakLabel")} value={n(data?.streak_days ?? 0)} />
            <Stat label={t("xpLabel")} value={n(data?.xp ?? 0)} />
          </View>

          {data?.next_chapter ? (
            <Pressable
              onPress={() => navigate("lessonDetail", { code: data.next_chapter!.code })}
            >
              <Card>
                <AppText weight="700" size={12} color={colors.accent}>
                  {t("nextChapterTitle")}
                </AppText>
                <AppText weight="800" size={17} style={{ marginTop: 4 }}>
                  {isFa ? data.next_chapter.name_fa : data.next_chapter.name_en}
                </AppText>
                <AppText muted weight="600" size={12} style={{ marginTop: 4 }}>
                  {(isFa ? data.next_chapter.group_name_fa : data.next_chapter.group_name_en) +
                    " · " +
                    data.next_chapter.code}
                </AppText>
              </Card>
            </Pressable>
          ) : null}

          <AppText weight="800" size={15} style={{ marginTop: spacing.xl, marginBottom: spacing.sm }}>
            {t("nextChapterHead")}
          </AppText>
          {(data?.focus_session.rows ?? []).map((row, i) => (
            <Card key={`${row.kind}-${i}`} style={{ marginBottom: spacing.sm }}>
              <AppText weight="700" size={14}>
                {isFa ? row.title_fa : row.title_en}
              </AppText>
              <AppText muted weight="600" size={12} style={{ marginTop: 3 }}>
                {isFa ? row.sub_fa : row.sub_en}
              </AppText>
              <AppText
                weight="800"
                size={12}
                color={colors.accent}
                style={{ marginTop: 6 }}
              >
                {n(row.minutes)} {isFa ? "دقیقه" : "min"}
              </AppText>
            </Card>
          ))}
        </>
      )}
    </Screen>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  const { colors } = useTheme();
  return (
    <Card style={{ flex: 1 }}>
      <AppText weight="900" size={22} color={colors.accent}>
        {value}
      </AppText>
      <AppText muted weight="600" size={12} style={{ marginTop: 2 }}>
        {label}
      </AppText>
    </Card>
  );
}
