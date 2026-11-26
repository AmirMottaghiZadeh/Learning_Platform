import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";

import { ReferenceFavorites } from "@/components/article/ReferenceFavorites";
import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem, MedscapeKind } from "@/api/types";
import { BrowseSearch } from "@/components/medscape/BrowseSearch";
import { FavoritesChip } from "@/components/medscape/FavoritesChip";
import { TopicRail } from "@/components/medscape/TopicRail";
import { LoadFailed } from "@/components/LoadFailed";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { spacing } from "@/theme/tokens";

function titleCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** The "diseasesConditions" screen's browse UX: search first, then every
 * specialty of the active category as a topic card. There is no second grid
 * underneath -- the cards are the list, and tapping one opens that specialty's
 * own A-Z article screen.
 *
 * There are ~3200 disease articles, too many to fetch as one list and group
 * client-side (the calculators approach), so the tree (category -> specialty
 * -> count) loads up front; a specialty's own article list loads lazily on its
 * own screen (MedscapeSpecialtyScreen).
 *
 * Order of the page follows design option 5 (2026-11-26): the search and the
 * topics are the reason the reader came, so they sit directly under the header,
 * and saved articles are a header chip instead of a block above them. */
export function MedscapeBrowseScreen() {
  const { t, n } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const kind: MedscapeKind = "disease";
  const titleKey: StringKey = "diseasesConditionsLabel";

  const initialQuery = useNav((s) => s.params.query);
  const [q, setQ] = useState(typeof initialQuery === "string" ? initialQuery : "");
  const query = useDebounced(q.trim());
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);

  const { data: tree, isLoading, isError, isFetching: treeFetching, refetch: refetchTree } = useQuery({
    queryKey: ["medscape-tree", kind],
    queryFn: () => medscapeApi.tree(kind),
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ["medscape-search", kind, query],
    queryFn: () => medscapeApi.search(kind, query),
    enabled: query.length >= 2,
  });

  useEffect(() => {
    if (tree && tree.length > 0 && !tree.some((node) => node.category === activeCategory)) {
      setActiveCategory(tree[0].category);
    }
  }, [tree, activeCategory]);

  useTour("diseases", (tree ?? []).length > 0);

  const openArticle = (slug: string) => navigate("medscapeOutline", { slug });
  const openSpecialty = (category: string, specialty: string) =>
    navigate("medscapeSpecialty", { kind, category, specialty });

  if (isLoading) return <LoadingState />;

  const node = (tree ?? []).find((item) => item.category === activeCategory) ?? (tree ?? [])[0];
  const specialties = node ? [...node.specialties].sort((a, b) => b.count - a.count) : [];
  const searching2 = query.length >= 2;

  return (
    <Screen>
      <ScreenChrome
        title={t(titleKey)}
        onBack={goBack}
        tour="diseases"
        actions={
          <FavoritesChip
            kind="disease"
            open={favoritesOpen}
            onToggle={() => setFavoritesOpen((open) => !open)}
          />
        }
      />

      {favoritesOpen && !q.trim() ? <ReferenceFavorites kind="disease" /> : null}

      <TourTarget id="dis.search" style={{ marginBottom: spacing.md }}>
        <BrowseSearch
          value={q}
          onChangeText={setQ}
          placeholder={t("medscapeSearchPlaceholder")}
          busy={searching}
        />
      </TourTarget>

      {searching2 ? (
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
      ) : isError || (tree ?? []).length === 0 ? (
        <LoadFailed message={t("medscapeTreeUnavailable")} onRetry={() => refetchTree()} busy={treeFetching} />
      ) : (
        <TourTarget id="dis.specialties" style={{ gap: 14 }}>
          {(tree ?? []).length > 1 ? (
            <View style={{ flexDirection: "row", backgroundColor: colors.pageBg, borderRadius: 12, padding: 3 }}>
              {(tree ?? []).map((item) => {
                const active = item.category === activeCategory;
                return (
                  <Pressable
                    key={item.category}
                    onPress={() => setActiveCategory(item.category)}
                    style={{ flex: 1 }}
                  >
                    <View
                      style={{
                        alignItems: "center",
                        paddingVertical: 8,
                        borderRadius: 9,
                        backgroundColor: active ? colors.accent : "transparent",
                      }}
                    >
                      <AppText weight={active ? "800" : "700"} size={12} color={active ? colors.onAccent : colors.muted}>
                        {titleCase(item.category)}
                      </AppText>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          ) : null}

          <TopicRail
            topics={specialties}
            onSelect={(name) => node && openSpecialty(node.category, name)}
            label={t("browseTopics")}
          />

        </TourTarget>
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
