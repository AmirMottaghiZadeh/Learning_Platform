import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem, MedscapeKind } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { specialtyIcon } from "@/utils/specialtyIcons";

function monogram(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function titleCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** The "diseasesConditions" screen's browse UX: category tabs over a
 * specialty grid. There are ~3200 disease articles, too many to fetch as
 * one list and group client-side (the calculators approach), so the tree
 * (category -> specialty -> count) loads up front; a specialty's own
 * article list loads lazily on its own screen (MedscapeSpecialtyScreen),
 * once that specialty tile is opened, as an A-Z index -- replacing what used
 * to be an inline accordion-of-an-accordion, which turned into an
 * unbounded, un-scannable flat list once a specialty had more than a
 * handful of articles (Dermatology alone has 400+).
 *
 * Guidelines use a different screen (MedscapeGuidelinesScreen): they have no
 * specialty taxonomy, just three flat content-type buckets, so this
 * category-tabs-over-a-grid shape doesn't apply to them. */
export function MedscapeBrowseScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const kind: MedscapeKind = "disease";
  const titleKey: StringKey = "diseasesConditionsLabel";

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const { data: tree, isLoading } = useQuery({
    queryKey: ["medscape-tree", kind],
    queryFn: () => medscapeApi.tree(kind),
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ["medscape-search", kind, query],
    queryFn: () => medscapeApi.search(kind, query),
    enabled: query.length >= 2,
  });

  useEffect(() => {
    if (tree && tree.length > 0 && !tree.some((n) => n.category === activeCategory)) {
      setActiveCategory(tree[0].category);
    }
  }, [tree, activeCategory]);

  const openArticle = (slug: string) => navigate("medscapeArticle", { slug });
  const openSpecialty = (category: string, specialty: string) =>
    navigate("medscapeSpecialty", { kind, category, specialty });

  if (isLoading) return <LoadingState />;

  const node = (tree ?? []).find((n) => n.category === activeCategory) ?? (tree ?? [])[0];
  const specialties = node ? [...node.specialties].sort((a, b) => b.count - a.count) : [];

  return (
    <Screen>
      <ScreenChrome title={t(titleKey)} onBack={goBack} />

      <View
        style={{
          flexDirection: row,
          alignItems: "center",
          gap: 8,
          backgroundColor: colors.inputBg,
          borderWidth: 1,
          borderColor: colors.trackBg,
          borderRadius: 14,
          paddingHorizontal: 14,
          paddingVertical: 12,
          marginBottom: spacing.lg,
        }}
      >
        <AppText muted>⌕</AppText>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder={t("medscapeSearchPlaceholder")}
          placeholderTextColor={colors.muted}
          style={{
            flex: 1,
            fontFamily: fontFamily("600"),
            fontSize: 13,
            color: colors.ink,
            textAlign: "left",
            writingDirection: "ltr",
            padding: 0,
          }}
        />
        {searching ? <AppText muted size={12}>…</AppText> : null}
      </View>

      {query.length >= 2 ? (
        !searching && (searchResults?.length ?? 0) === 0 ? (
          <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
            {t("medscapeEmptyTitle")} — {t("medscapeEmptySub")}
          </AppText>
        ) : (
          <View style={{ gap: 8 }}>
            {(searchResults ?? []).map((a) => (
              <ArticleRow key={a.slug} article={a} onPress={() => openArticle(a.slug)} />
            ))}
          </View>
        )
      ) : (
        <View style={{ gap: 14 }}>
          {(tree ?? []).length > 1 ? (
            <View style={{ flexDirection: row, backgroundColor: colors.pageBg, borderRadius: 12, padding: 3 }}>
              {(tree ?? []).map((n) => {
                const active = n.category === activeCategory;
                return (
                  <Pressable key={n.category} onPress={() => setActiveCategory(n.category)} style={{ flex: 1 }}>
                    <View
                      style={{
                        alignItems: "center",
                        paddingVertical: 8,
                        borderRadius: 9,
                        backgroundColor: active ? colors.accent : "transparent",
                      }}
                    >
                      <AppText weight={active ? "800" : "700"} size={12} color={active ? colors.onAccent : colors.muted}>
                        {titleCase(n.category)}
                      </AppText>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          ) : null}

          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10 }}>
            {specialties.map((sp) => (
              <Pressable
                key={sp.name}
                onPress={() => openSpecialty(node!.category, sp.name)}
                style={{ width: "48%" }}
              >
                <View
                  style={{
                    backgroundColor: colors.cardBg,
                    borderRadius: 14,
                    borderWidth: 1,
                    borderColor: colors.border,
                    padding: 13,
                    gap: 8,
                  }}
                >
                  {specialtyIcon(sp.name) ? (
                    <IconImage name={specialtyIcon(sp.name)!} size={34} />
                  ) : (
                    <View
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 10,
                        backgroundColor: colors.accent + "1A",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <AppText weight="800" size={11} color={colors.accent}>
                        {monogram(sp.name)}
                      </AppText>
                    </View>
                  )}
                  <AppText
                    weight="800"
                    size={12.5}
                    numberOfLines={2}
                    style={{ lineHeight: 16, textAlign: "left", writingDirection: "ltr" }}
                  >
                    {sp.name}
                  </AppText>
                  <AppText muted weight="700" size={11} style={{ textAlign: "left", writingDirection: "ltr" }}>
                    {sp.count} {t("medscapeArticleCount")}
                  </AppText>
                </View>
              </Pressable>
            ))}
          </View>
        </View>
      )}
    </Screen>
  );
}

function ArticleRow({ article, onPress }: { article: MedscapeArticleListItem; onPress: () => void }) {
  return (
    <Pressable onPress={onPress}>
      <Card soft style={{ gap: 0 }}>
        <AppText weight="700" size={13.5} style={{ textAlign: "left", writingDirection: "ltr" }}>
          {article.title}
        </AppText>
      </Card>
    </Pressable>
  );
}
