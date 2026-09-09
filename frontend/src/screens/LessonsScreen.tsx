import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";

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

export function LessonsScreen() {
  const { t, isFa, n } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });

  if (isLoading) return <LoadingState />;

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenHeader title={t("lessonsTitle")} />
      {isError ? (
        <Card>
          <AppText weight="700" color={colors.denyLabel}>
            {t("loadFailed")}
          </AppText>
        </Card>
      ) : (
        (data ?? []).map((group) => (
          <View key={group.code} style={{ marginBottom: spacing.lg }}>
            <AppText weight="800" size={14} style={{ marginBottom: spacing.sm }}>
              {isFa ? group.name_fa : group.name_en}
            </AppText>
            {group.subgroups.map((sub) => {
              const pct = sub.total ? Math.round((sub.done / sub.total) * 100) : 0;
              return (
                <Pressable
                  key={sub.code}
                  onPress={() => navigate("lessonDetail", { code: sub.code })}
                >
                  <Card style={{ marginBottom: spacing.sm }}>
                    <View
                      style={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <View style={{ flex: 1 }}>
                        <AppText weight="700" size={14}>
                          {isFa ? sub.name_fa : sub.name_en}
                        </AppText>
                        <AppText muted weight="600" size={12} style={{ marginTop: 2 }}>
                          {n(sub.done)}/{n(sub.total)} {t("lessonsUnit")}
                        </AppText>
                      </View>
                      <AppText weight="800" size={13} color={colors.accent}>
                        {n(pct)}%
                      </AppText>
                    </View>
                    <View
                      style={{
                        height: 4,
                        borderRadius: 2,
                        backgroundColor: colors.trackBg,
                        marginTop: 10,
                        overflow: "hidden",
                      }}
                    >
                      <View
                        style={{
                          width: `${Math.max(3, pct)}%`,
                          height: 4,
                          backgroundColor: colors.accent,
                        }}
                      />
                    </View>
                  </Card>
                </Pressable>
              );
            })}
          </View>
        ))
      )}
    </Screen>
  );
}
