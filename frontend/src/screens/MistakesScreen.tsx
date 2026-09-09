import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { Mistake } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function MistakesScreen() {
  const { t, isFa, n } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState<number | null>(null);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ["mistakes"],
    queryFn: meApi.mistakes,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["mistakes"] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
  };
  const resolve = useMutation({ mutationFn: meApi.resolveMistake, onSuccess: invalidate });
  const restore = useMutation({ mutationFn: meApi.restoreMistakes, onSuccess: invalidate });

  if (isLoading) return <LoadingState />;

  const unresolved = (data ?? []).filter((m) => !m.resolved);

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenChrome title={t("mistakesTitle")} onBack={goBack} />

      {unresolved.length === 0 ? (
        <View style={{ alignItems: "center", paddingVertical: 48, paddingHorizontal: 16 }}>
          <View
            style={{
              width: 64,
              height: 64,
              borderRadius: 20,
              backgroundColor: colors.softBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 16,
            }}
          >
            <AppText size={28} color={colors.accent}>
              ✓
            </AppText>
          </View>
          <AppText weight="800" size={16} center>
            {t("mistakesEmptyTitle")}
          </AppText>
          <AppText muted weight="600" size={13} center style={{ marginTop: 8, lineHeight: 22 }}>
            {t("mistakesEmptySub")}
          </AppText>
          {(data ?? []).some((m) => m.resolved) ? (
            <Pressable
              onPress={() => restore.mutate()}
              style={{
                marginTop: 18,
                height: 44,
                paddingHorizontal: 22,
                borderRadius: 999,
                borderWidth: 1,
                borderColor: colors.trackBg,
                backgroundColor: colors.softBg,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AppText weight="800" size={13} color={colors.accent}>
                {t("mistakesRestore")}
              </AppText>
            </Pressable>
          ) : null}
        </View>
      ) : (
        <View style={{ gap: 10 }}>
          {unresolved.map((m: Mistake) => (
            <Card key={m.id}>
              <Pressable
                onPress={() => setExpanded(expanded === m.id ? null : m.id)}
                style={{ flexDirection: "row", alignItems: "center", gap: 10 }}
              >
                <View
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 11,
                    backgroundColor: colors.softBg,
                    borderWidth: 1,
                    borderColor: colors.trackBg,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <IconImage name="pillWarning" size={24} />
                </View>
                <View style={{ flex: 1 }}>
                  <AppText weight="800" size={14}>
                    {isFa ? m.topic_fa : m.topic_en}
                  </AppText>
                  <AppText weight="700" size={12} muted style={{ marginTop: 2 }}>
                    {isFa ? `${n(m.count)} بار` : `${m.count} times`}
                  </AppText>
                </View>
                <AppText weight="800" size={17} color={colors.denyLabel}>
                  {n(m.count)}
                </AppText>
              </Pressable>

              {expanded === m.id ? (
                <View style={{ marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: colors.trackBg }}>
                  <AppText muted weight="600" size={12} style={{ lineHeight: 20 }}>
                    {isFa ? m.detail_fa : m.detail_en}
                  </AppText>
                  <Pressable
                    onPress={() => resolve.mutate(m.id)}
                    style={{
                      marginTop: 12,
                      height: 42,
                      borderRadius: 12,
                      borderWidth: 1,
                      borderColor: colors.trackBg,
                      backgroundColor: colors.softBg,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <AppText weight="800" size={13} color={colors.accent}>
                      {t("mistakeResolve")}
                    </AppText>
                  </Pressable>
                </View>
              ) : null}
            </Card>
          ))}
        </View>
      )}
    </Screen>
  );
}
