import React, { useEffect, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { Pressable, View } from "react-native";

import { lessonsApi, medscapeApi } from "@/api/endpoints";
import { MedscapeKind } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Chevron } from "@/components/primitives/Chevron";
import { Input } from "@/components/primitives/Input";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { ScreenKey } from "@/navigation/types";
import { uptodateSource } from "@/offline/sources";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { squircle } from "@/theme/squircle";
import { radius, spacing } from "@/theme/tokens";
import { stripHtml } from "@/utils/html";

const RESULT_PREVIEW_LIMIT = 5;
const QUERY_LIMIT = 120;

const SCOPES = [
  ["all", "resourceLookupAll"],
  ["drugs", "resourceLookupDrugs"],
  ["articles", "resourceLookupArticles"],
] as const;

type Scope = (typeof SCOPES)[number][0];

type Hit = {
  id: string;
  title: string;
  nameFa?: string;
  target: ScreenKey;
  params: Record<string, string>;
};

type Source = {
  key: string;
  scope: Exclude<Scope, "all">;
  label: StringKey | "UpToDate";
  provider?: "Medscape";
  target: ScreenKey;
  search: (query: string) => Promise<Hit[]>;
};

async function searchMedscape(kind: MedscapeKind, query: string): Promise<Hit[]> {
  return (await medscapeApi.search(kind, query)).map((article) => ({
    id: article.slug,
    title: stripHtml(article.title),
    target: "medscapeOutline",
    params: { slug: article.slug },
  }));
}

const SOURCES: Source[] = [
  {
    key: "lesson-search",
    scope: "drugs",
    label: "lessonsLabel",
    target: "lessons",
    search: async (query) => (await lessonsApi.search(query)).flatMap((drug) => {
      const chapter = drug.chapters[0];
      return chapter ? [{
        id: drug.slug,
        title: drug.name,
        nameFa: drug.name_fa,
        target: "lessonDetail",
        params: { slug: drug.slug, code: chapter.code },
      }] : [];
    }),
  },
  {
    key: "uptodate-search-page",
    scope: "articles",
    label: "UpToDate",
    target: "uptodate",
    search: async (query) => (await uptodateSource.search(query, RESULT_PREVIEW_LIMIT + 1)).map((article) => {
      const title = stripHtml(article.title);
      return { id: article.id, title, target: "uptodateOutline", params: { id: article.id, title } };
    }),
  },
  {
    key: "reference-diseases",
    scope: "articles",
    label: "diseasesConditionsLabel",
    provider: "Medscape",
    target: "diseasesConditions",
    search: (query) => searchMedscape("disease", query),
  },
  {
    key: "reference-guidelines",
    scope: "articles",
    label: "guidelinesLabel",
    provider: "Medscape",
    target: "guidelines",
    search: (query) => searchMedscape("guideline", query),
  },
];

export function ResourceLookup() {
  const { t, row, isFa } = useLang();
  const { colors } = useTheme();
  const userId = useAuth((state) => state.user?.id);
  const params = useNav((state) => state.params);
  const setParams = useNav((state) => state.setParams);
  const navigate = useNav((state) => state.navigate);
  const query = typeof params.query === "string" ? params.query : "";
  const scope = params.scope === "drugs" || params.scope === "articles" ? params.scope : "all";
  const [draft, setDraft] = useState(query);
  const [short, setShort] = useState(false);

  // The initial URL destination and Back both restore the submitted query.
  useEffect(() => setDraft(query), [query]);

  const sources = SOURCES.filter((source) => scope === "all" || source.scope === scope);
  const searching = query.length >= 2;
  const results = useQueries({
    queries: sources.map((source) => ({
      queryKey: [source.key, "unified", userId, query],
      queryFn: () => source.search(query),
      enabled: searching,
      staleTime: 30_000,
      retry: false,
    })),
  });
  const pending = results.some((result) => result.isPending);
  const failed = results.filter((result) => result.isError);
  const hasResults = results.some((result) => Boolean(result.data?.length));

  const submit = () => {
    const value = draft.trim();
    setShort(value.length < 2);
    if (value.length < 2) return;
    if (value === query) {
      for (const result of results) void result.refetch();
    } else {
      setParams({ query: value });
    }
  };

  const selectScope = (next: Scope) => {
    const value = draft.trim();
    setParams(value.length >= 2 ? { scope: next, query: value } : { scope: next });
  };

  return (
    <View style={{ gap: spacing.lg }}>
      <Card raised style={{ gap: spacing.sm }}>
        <AppText accessibilityRole="header" aria-level={1} weight="900" size={17}>
          {t("resourceLookupTitle")}
        </AppText>
        <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
          <View style={{ flex: 1, minWidth: 0 }}>
            <Input
              testID="resource-lookup-query"
              accessibilityLabel={t("resourceLookupHint")}
              placeholder={t("resourceLookupPlaceholder")}
              value={draft}
              onChangeText={(value) => {
                setDraft(value);
                setShort(false);
                if (!value.trim() && query) setParams({ query: "" });
              }}
              maxLength={QUERY_LIMIT}
              autoCorrect={false}
              autoCapitalize="none"
              returnKeyType="search"
              onSubmitEditing={submit}
            />
          </View>
          <Button
            full={false}
            label={t("resourceLookupSubmit")}
            onPress={submit}
            style={{ minHeight: 48, alignSelf: "stretch", paddingHorizontal: spacing.md }}
          />
        </View>
        {short ? (
          <AppText accessibilityRole="alert" size={13} color={colors.denyLabel}>{t("resourceLookupShort")}</AppText>
        ) : null}
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
          {SCOPES.map(([key, name]) => {
            const selected = scope === key;
            return (
              <Pressable
                key={key}
                accessibilityRole="button"
                accessibilityLabel={t(name)}
                accessibilityState={{ selected }}
                onPress={() => selectScope(key)}
                style={({ pressed }) => ({
                  ...squircle,
                  minHeight: 44,
                  justifyContent: "center",
                  borderRadius: radius.sm,
                  paddingHorizontal: spacing.md,
                  backgroundColor: selected ? colors.leitnerActiveBg : "transparent",
                  opacity: pressed ? 0.8 : 1,
                })}
              >
                <AppText weight={selected ? "700" : "500"} size={13} color={selected ? colors.accent : colors.muted}>
                  {t(name)}
                </AppText>
              </Pressable>
            );
          })}
          <Pressable
            testID="resource-lookup-smart-search"
            accessibilityRole="button"
            onPress={() => navigate("aiLab")}
            style={({ pressed }) => ({
              ...squircle,
              flexDirection: row,
              alignItems: "center",
              gap: spacing.xs,
              minHeight: 44,
              paddingHorizontal: spacing.md,
              borderRadius: radius.sm,
              backgroundColor: colors.softBg,
              opacity: pressed ? 0.8 : 1,
            })}
          >
            <AppText weight="800" size={13} color={colors.accent}>{t("resourceLookupSmart")}</AppText>
            <Chevron color={colors.accent} />
          </Pressable>
        </View>
      </Card>

      <View style={{ gap: spacing.lg }}>
        {searching ? (
          <View testID="resource-lookup-results" style={{ minWidth: 0, gap: spacing.sm }}>
            <AppText accessibilityRole="header" aria-level={2} size={17} weight="800">{t("resourceLookupResults")}</AppText>
            {results.map((result, index) => {
              if (!result.data?.length) return null;
              const source = sources[index];
              const label = source.label === "UpToDate" ? source.label : t(source.label);
              return (
                <Card key={source.key} padded={false} style={{ paddingHorizontal: spacing.md }}>
                  <AppText muted weight="700" size={12} style={{ paddingTop: spacing.sm }}>
                    {source.provider ? `${label} · ${source.provider}` : label}
                  </AppText>
                  {result.data.slice(0, RESULT_PREVIEW_LIMIT).map((hit) => {
                    const title = isFa && hit.nameFa ? hit.nameFa : hit.title;
                    return (
                      <Pressable
                        key={hit.id}
                        accessibilityRole="button"
                        onPress={() => navigate(hit.target, hit.params)}
                        style={({ pressed }) => ({
                          minHeight: 48, flexDirection: row, alignItems: "center", gap: spacing.sm,
                          paddingVertical: spacing.sm, borderBottomWidth: 1, borderColor: colors.border,
                          opacity: pressed ? 0.72 : 1,
                        })}
                      >
                        <View style={{ flex: 1, minWidth: 0 }}>
                          <AppText weight="700" size={14}>{title}</AppText>
                          {title !== hit.title ? <AppText muted size={12}>{hit.title}</AppText> : null}
                        </View>
                        <Chevron />
                      </Pressable>
                    );
                  })}
                  {result.data.length > RESULT_PREVIEW_LIMIT ? (
                    <Button variant="ghost" full={false} label={t("resourceLookupBrowse")} onPress={() => navigate(source.target, { query })} />
                  ) : null}
                </Card>
              );
            })}
            {pending ? <AppText muted accessibilityLiveRegion="polite">{t("resourceLookupPending")}</AppText> : null}
            {!pending && !hasResults && !failed.length ? (
              <Card><AppText muted accessibilityLiveRegion="polite">{t("resourceLookupEmpty")}</AppText></Card>
            ) : null}
            {failed.length ? (
              <Card>
                <AppText accessibilityRole="alert" color={colors.denyLabel}>
                  {t(failed.length === sources.length ? "loadFailed" : "resourceLookupPartial")}
                </AppText>
                <Button variant="ghost" full={false} label={t("retry")} onPress={() => {
                  for (const result of failed) void result.refetch();
                }} />
              </Card>
            ) : null}
          </View>
        ) : null}
      </View>
    </View>
  );
}
