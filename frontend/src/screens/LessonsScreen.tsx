import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
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

type Category = {
  code: string;
  name_fa: string;
  name_en: string;
  topics: LessonGroup[];
};

/** The API already lists topics in category-clustered order (see
 * apps.lessons.data.study_topics), so a stable first-seen grouping here needs
 * no separate categories request. */
function groupByCategory(groups: LessonGroup[]): Category[] {
  const byCode = new Map<string, Category>();
  for (const group of groups) {
    let category = byCode.get(group.category_code);
    if (!category) {
      category = {
        code: group.category_code,
        name_fa: group.category_name_fa,
        name_en: group.category_name_en,
        topics: [],
      };
      byCode.set(group.category_code, category);
    }
    category.topics.push(group);
  }
  return [...byCode.values()];
}

export function LessonsScreen() {
  const { t } = useLang();
  const { colors } = useTheme();
  const [openCategory, setOpenCategory] = useState<string | null>(null);
  const [openTopic, setOpenTopic] = useState<string | null>(null);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });

  const categories = useMemo(() => groupByCategory(data ?? []), [data]);

  if (isLoading) return <LoadingState />;

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenChrome title={t("lessonsTitle")} help="lessons" />
      {isError ? (
        <Card>
          <AppText weight="700" color={colors.denyLabel}>
            {t("loadFailed")}
          </AppText>
        </Card>
      ) : (
        categories.map((category) => (
          <CategoryCard
            key={category.code}
            category={category}
            isOpen={openCategory === category.code}
            onToggle={() => setOpenCategory(openCategory === category.code ? null : category.code)}
            openTopic={openTopic}
            onToggleTopic={(code) => setOpenTopic((cur) => (cur === code ? null : code))}
          />
        ))
      )}
    </Screen>
  );
}

/** The outer accordion: a body-system/domain (e.g. "Cardiovascular & blood")
 * holding a handful of clinical topics — so a learner picks a system first
 * instead of scanning 50+ topics in one flat list. */
function CategoryCard({
  category,
  isOpen,
  onToggle,
  openTopic,
  onToggleTopic,
}: {
  category: Category;
  isOpen: boolean;
  onToggle: () => void;
  openTopic: string | null;
  onToggleTopic: (code: string) => void;
}) {
  const { colors, shadows } = useTheme();
  const { isFa, n, row } = useLang();

  const total = category.topics.reduce(
    (a, g) => a + g.subgroups.reduce((b, s) => b + s.total, 0),
    0,
  );
  const done = category.topics.reduce(
    (a, g) => a + g.subgroups.reduce((b, s) => b + s.done, 0),
    0,
  );
  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <View
      style={[
        {
          backgroundColor: colors.cardBg,
          borderRadius: 18,
          borderWidth: 1,
          borderColor: colors.border,
          marginBottom: spacing.md,
          overflow: "hidden",
        },
        shadows.raisedSm,
      ]}
    >
      <Pressable
        onPress={onToggle}
        style={{ padding: 16, flexDirection: row, alignItems: "center", gap: 12 }}
      >
        <View
          style={{
            width: 42,
            height: 42,
            borderRadius: 13,
            backgroundColor: colors.accent + "1a",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AppText weight="900" size={16} color={colors.accent}>
            {n(category.topics.length)}
          </AppText>
        </View>
        <View style={{ flex: 1 }}>
          <AppText weight="900" size={15}>
            {isFa ? category.name_fa : category.name_en}
          </AppText>
          <AppText muted weight="600" size={12} style={{ marginTop: 2 }}>
            {n(category.topics.length)} {isFa ? "موضوع" : "topics"} · {n(done)}/{n(total)}
          </AppText>
          <View
            style={{
              height: 5,
              borderRadius: 3,
              backgroundColor: colors.trackBg,
              marginTop: 9,
              overflow: "hidden",
            }}
          >
            <View style={{ width: `${Math.max(3, pct)}%`, height: 5, backgroundColor: colors.accent }} />
          </View>
        </View>
        <AppText muted size={13} weight="800">
          {isOpen ? "▲" : "▼"}
        </AppText>
      </Pressable>

      {isOpen ? (
        <View style={{ paddingHorizontal: 12, paddingBottom: 12, gap: 8 }}>
          {category.topics.map((topic) => (
            <GroupCard
              key={topic.code}
              group={topic}
              isOpen={openTopic === topic.code}
              onToggle={() => onToggleTopic(topic.code)}
            />
          ))}
        </View>
      ) : null}
    </View>
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
  const { isFa, n, row } = useLang();
  const navigate = useNav((s) => s.navigate);

  const total = group.subgroups.reduce((a, s) => a + s.total, 0);
  const done = group.subgroups.reduce((a, s) => a + s.done, 0);
  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <View
      style={{
        backgroundColor: colors.softBg,
        borderRadius: 14,
        borderWidth: 1,
        borderColor: colors.border,
        overflow: "hidden",
      }}
    >
      <Pressable
        onPress={onToggle}
        style={{ padding: 12, flexDirection: row, alignItems: "flex-start", gap: 10 }}
      >
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
        <View style={{ paddingHorizontal: 12, paddingBottom: 12, gap: 6 }}>
          {group.subgroups.map((sub) => {
            const sp = sub.total ? sub.done / sub.total : 0;
            return (
              <Pressable
                key={sub.code}
                onPress={() => navigate("lessonList", { code: sub.code })}
                style={{
                  backgroundColor: colors.cardBg,
                  borderRadius: 12,
                  padding: 11,
                  overflow: "hidden",
                }}
              >
                <View
                  style={{
                    position: "absolute",
                    ...(isFa ? { right: 0 } : { left: 0 }),
                    top: 0,
                    bottom: 0,
                    width: `${sp * 100}%`,
                    backgroundColor: colors.leitnerActiveBg,
                  }}
                />
                <View
                  style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center" }}
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
