import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { LessonGroup } from "@/api/types";
import { spacing } from "@/theme/tokens";

export function LessonsScreen() {
  const { t, isFa, n } = useLang();
  const { colors } = useTheme();
  const [open, setOpen] = useState<string | null>(null);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });

  if (isLoading) return <LoadingState />;

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenChrome title={t("lessonsTitle")} />
      {isError ? (
        <Card>
          <AppText weight="700" color={colors.denyLabel}>
            {t("loadFailed")}
          </AppText>
        </Card>
      ) : (
        (data ?? []).map((group) => (
          <GroupCard
            key={group.code}
            group={group}
            isOpen={open === group.code}
            onToggle={() => setOpen(open === group.code ? null : group.code)}
          />
        ))
      )}
    </Screen>
  );
}

function GroupCard({
  group,
  isOpen,
  onToggle,
}: {
  group: LessonGroup;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const { colors, shadows } = useTheme();
  const { isFa, n } = useLang();
  const navigate = useNav((s) => s.navigate);

  const total = group.subgroups.reduce((a, s) => a + s.total, 0);
  const done = group.subgroups.reduce((a, s) => a + s.done, 0);
  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <View
      style={[
        {
          backgroundColor: colors.cardBg,
          borderRadius: 16,
          borderWidth: 1,
          borderColor: colors.border,
          marginBottom: spacing.sm,
          overflow: "hidden",
        },
        shadows.raisedSm,
      ]}
    >
      <Pressable
        onPress={onToggle}
        style={{ padding: 14, flexDirection: "row", alignItems: "flex-start", gap: 10 }}
      >
        <View
          style={{
            width: 36,
            height: 36,
            borderRadius: 11,
            backgroundColor: colors.accent + "1a",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AppText weight="900" size={14} color={colors.accent}>
            {group.code}
          </AppText>
        </View>
        <View style={{ flex: 1 }}>
          <AppText weight="800" size={13}>
            {isFa ? group.name_fa : group.name_en}
          </AppText>
          <AppText muted weight="600" size={12} style={{ marginTop: 1 }}>
            {n(group.subgroups.length)} {isFa ? "زیرگروه" : "subgroups"} · {n(done)}/{n(total)}
          </AppText>
          <View
            style={{
              height: 4,
              borderRadius: 2,
              backgroundColor: colors.trackBg,
              marginTop: 8,
              overflow: "hidden",
            }}
          >
            <View style={{ width: `${Math.max(3, pct)}%`, height: 4, backgroundColor: colors.accent }} />
          </View>
        </View>
        <AppText muted size={12} weight="800">
          {isOpen ? "▲" : "▼"}
        </AppText>
      </Pressable>

      {isOpen ? (
        <View style={{ paddingHorizontal: 14, paddingBottom: 12, gap: 6 }}>
          {group.subgroups.map((sub) => {
            const sp = sub.total ? sub.done / sub.total : 0;
            return (
              <Pressable
                key={sub.code}
                onPress={() => navigate("lessonList", { code: sub.code })}
                style={{
                  backgroundColor: colors.softBg,
                  borderRadius: 12,
                  padding: 11,
                  overflow: "hidden",
                }}
              >
                <View
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: `${sp * 100}%`,
                    backgroundColor: colors.leitnerActiveBg,
                  }}
                />
                <View
                  style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}
                >
                  <AppText weight="700" size={12}>
                    {sub.code} — {isFa ? sub.name_fa : sub.name_en}
                  </AppText>
                  <AppText weight="800" size={12} color={sp >= 1 ? colors.accent : colors.muted}>
                    {n(sub.done)}/{n(sub.total)}
                  </AppText>
                </View>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}
