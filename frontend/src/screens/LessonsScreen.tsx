import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, iconFor } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { LessonDrugSearchResult, LessonGroup } from "@/api/types";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { LessonCategory, groupByCategory } from "@/utils/lessonCategories";

export function LessonsScreen() {
  const { t, isFa, row } = useLang();
  const { colors } = useTheme();
  const [openCategory, setOpenCategory] = useState<string | null>(null);
  const [openTopic, setOpenTopic] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const query = useDebounced(q.trim(), 250);
  const searching = query.length >= 2;

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });
  const { data: hits, isFetching: hitsLoading, isError: hitsError } = useQuery({
    queryKey: ["lesson-search", query],
    queryFn: () => lessonsApi.search(query),
    enabled: searching,
    staleTime: 5 * 60_000,
  });

  const categories = useMemo(() => groupByCategory(data ?? []), [data]);

  if (isLoading) return <LoadingState />;

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenChrome title={t("lessonsTitle")} help="lessons" />
      <View
        style={{
          flexDirection: row,
          alignItems: "center",
          gap: 8,
          backgroundColor: colors.inputBg,
          borderWidth: 1,
          borderColor: q ? colors.accent : colors.trackBg,
          borderRadius: 14,
          paddingHorizontal: 14,
          paddingVertical: 11,
          marginBottom: spacing.md,
        }}
      >
        <AppText weight="800" size={16} color={q ? colors.accent : colors.muted} style={{ lineHeight: 20 }}>
          ⌕
        </AppText>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder={t("lessonsSearchPlaceholder")}
          placeholderTextColor={colors.muted}
          autoCorrect={false}
          autoCapitalize="none"
          returnKeyType="search"
          style={{
            flex: 1,
            fontFamily: fontFamily("600"),
            fontSize: 14,
            color: colors.ink,
            textAlign: isFa ? "right" : "left",
            padding: 0,
          }}
        />
        {hitsLoading && searching ? (
          <AppText muted size={12}>
            …
          </AppText>
        ) : q ? (
          <Pressable onPress={() => setQ("")} hitSlop={10} accessibilityLabel="clear">
            <AppText muted weight="700" size={17} style={{ lineHeight: 20 }}>
              ×
            </AppText>
          </Pressable>
        ) : null}
      </View>

      {searching ? (
        <DrugSearchResults hits={hits} loading={hitsLoading && !hits} failed={hitsError} />
      ) : isError ? (
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

/** The drug search's answers, in place of the topic list while a query is
 * typed: each drug's name in both languages, opening its lesson in its first
 * chapter -- or, for a drug taught in several, in whichever chapter is tapped. */
function DrugSearchResults({
  hits,
  loading,
  failed,
}: {
  hits: LessonDrugSearchResult[] | undefined;
  loading: boolean;
  failed: boolean;
}) {
  const { t, isFa, row } = useLang();
  const { colors, shadows } = useTheme();
  const navigate = useNav((s) => s.navigate);

  if (loading) return <LoadingState />;
  if (failed) {
    return (
      <AppText weight="700" color={colors.denyLabel} style={{ paddingVertical: 12 }}>
        {t("loadFailed")}
      </AppText>
    );
  }
  if (!hits || hits.length === 0) {
    return (
      <AppText muted weight="600" size={13} center style={{ paddingVertical: 24 }}>
        {t("lessonsSearchEmpty")}
      </AppText>
    );
  }

  const open = (slug: string, code: string) => navigate("lessonDetail", { code, slug });

  return (
    <View style={{ gap: 8 }}>
      {hits.map((hit) => {
        const primary = isFa ? hit.name_fa || hit.name : hit.name;
        const secondary = isFa ? (hit.name_fa ? hit.name : "") : hit.name_fa;
        return (
          <View
            key={hit.slug}
            style={[
              { backgroundColor: colors.cardBg, borderRadius: 16, borderWidth: 1, borderColor: colors.border },
              shadows.raisedSm,
            ]}
          >
            <Pressable
              onPress={() => open(hit.slug, hit.chapters[0].code)}
              style={{ flexDirection: row, alignItems: "center", gap: 10, padding: 14 }}
            >
              <View style={{ flex: 1 }}>
                <AppText weight="800" size={15}>
                  {primary}
                </AppText>
                {secondary ? (
                  <AppText muted weight="600" size={12.5} style={{ marginTop: 1 }}>
                    {secondary}
                  </AppText>
                ) : null}
              </View>
              {hit.chapters.length === 1 ? (
                <AppText muted weight="700" size={11.5} numberOfLines={1} style={{ maxWidth: "45%" }}>
                  {isFa ? hit.chapters[0].name_fa : hit.chapters[0].name_en}
                </AppText>
              ) : null}
              <AppText muted size={14}>
                {isFa ? "‹" : "›"}
              </AppText>
            </Pressable>
            {hit.chapters.length > 1 ? (
              <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6, paddingHorizontal: 14, paddingBottom: 12 }}>
                {hit.chapters.map((chapter) => (
                  <Pressable
                    key={chapter.code}
                    onPress={() => open(hit.slug, chapter.code)}
                    style={{
                      paddingHorizontal: 10,
                      paddingVertical: 4,
                      borderRadius: 999,
                      backgroundColor: colors.accent + "14",
                    }}
                  >
                    <AppText weight="700" size={11.5} color={colors.accent}>
                      {isFa ? chapter.name_fa : chapter.name_en}
                    </AppText>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </View>
        );
      })}
    </View>
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
  category: LessonCategory;
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
  const categoryIcon = iconFor(`cat-${category.code}`);

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
          {categoryIcon ? (
            <IconImage name={categoryIcon} size={30} />
          ) : (
            <AppText weight="900" size={16} color={colors.accent}>
              {n(category.topics.length)}
            </AppText>
          )}
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
  const { colors } = useTheme();
  const { isFa, n, row } = useLang();
  const navigate = useNav((s) => s.navigate);

  const total = group.subgroups.reduce((a, s) => a + s.total, 0);
  const done = group.subgroups.reduce((a, s) => a + s.done, 0);
  const pct = total ? Math.round((done / total) * 100) : 0;
  const topicIcon = iconFor(`topic-${group.code}`);

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
        style={{ padding: 12, flexDirection: row, alignItems: "center", gap: 10 }}
      >
        {topicIcon ? <IconImage name={topicIcon} size={34} /> : null}
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
