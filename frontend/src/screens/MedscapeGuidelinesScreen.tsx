import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { ReferenceFavorites } from "@/components/article/ReferenceFavorites";
import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem } from "@/api/types";
import { AlphabeticalArticleList } from "@/components/AlphabeticalArticleList";
import { BrowseSearch } from "@/components/medscape/BrowseSearch";
import { FavoritesChip } from "@/components/medscape/FavoritesChip";
import { TopicRail } from "@/components/medscape/TopicRail";
import { LoadFailed } from "@/components/LoadFailed";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { layout, spacing } from "@/theme/tokens";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatMonthYear(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/** Guidelines have no specialty taxonomy the way diseases do -- the source
 * gives three flat content-type buckets (Guidelines/Expert Insights/Primary
 * Care Hacks) with no secondary grouping.
 *
 * The screen is list-first (design option 5, 2026-11-26): search, then the
 * three buckets as topic cards with their article counts, then the A-Z list.
 * Saved articles are a header chip rather than a block, and the "recently
 * updated" spotlight is collapsed behind a chip -- both used to sit above the
 * search and push the list itself below the fold on a phone. */
export function MedscapeGuidelinesScreen() {
  const { t, n } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [activeSpecialty, setActiveSpecialty] = useState<string | null>(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [showRecent, setShowRecent] = useState(false);
  const initialQuery = useNav((s) => s.params.query);
  const [q, setQ] = useState(typeof initialQuery === "string" ? initialQuery : "");
  const plannedTopic = typeof initialQuery === "string" && initialQuery.trim().length > 0;
  const plannedQuery = useDebounced(q.trim());
  const topicResults = useQuery({
    queryKey: ["medscape-search", "guideline", plannedQuery],
    queryFn: () => medscapeApi.search("guideline", plannedQuery),
    enabled: plannedTopic && plannedQuery.length >= 2,
  });

  const {
    data: tree,
    isLoading: treeLoading,
    isError: treeError,
    isFetching: treeFetching,
    refetch: refetchTree,
  } = useQuery({
    queryKey: ["medscape-tree", "guideline"],
    queryFn: () => medscapeApi.tree("guideline"),
    enabled: !plannedTopic,
  });

  const node = tree?.[0];
  const specialties = node ? [...node.specialties].sort((a, b) => b.count - a.count) : [];

  useEffect(() => {
    if (specialties.length > 0 && !specialties.some((s) => s.name === activeSpecialty)) {
      setActiveSpecialty(specialties[0].name);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [specialties.map((s) => s.name).join(","), activeSpecialty]);

  const category = node?.category ?? "guideline";
  const specialty = activeSpecialty ?? "";

  const { data: items, isLoading: itemsLoading } = useQuery({
    queryKey: ["medscape-articles", "guideline", category, specialty],
    queryFn: () => medscapeApi.bySpecialty("guideline", category, specialty),
    enabled: !!specialty,
  });

  const { data: recent } = useQuery({
    queryKey: ["medscape-recent", "guideline", category, specialty],
    queryFn: () => medscapeApi.recentlyUpdated("guideline", category, specialty, 8),
    enabled: !!specialty,
  });

  const all = items ?? [];
  const query = q.trim().toLowerCase();
  const filtered = query.length > 0 ? all.filter((a) => a.title.toLowerCase().includes(query)) : all;

  const openArticle = (slug: string) => navigate("medscapeOutline", { slug });
  useTour("guidelines", !itemsLoading && all.length > 0);

  if (plannedTopic) {
    const placeholder = t("medscapeSearchPlaceholder");
    return (
      <Screen scroll={false} contentStyle={{ gap: spacing.md }} keyboardShouldPersistTaps="handled">
        <ScreenChrome title={t("guidelinesLabel")} onBack={goBack} />
        <BrowseSearch value={q} onChangeText={setQ} placeholder={placeholder} busy={topicResults.isFetching} />
        {q.trim().length < 2 ? <AppText muted>{t("resourceLookupShort")}</AppText>
          : q.trim() !== plannedQuery || topicResults.isPending ? <LoadingState />
          : topicResults.isError ? <LoadFailed message={t("loadFailed")} onRetry={() => void topicResults.refetch()} />
          : <AlphabeticalArticleList items={topicResults.data ?? []} onPressItem={openArticle} emptyText={t("medscapeNoLocalResults")} />}
      </Screen>
    );
  }

  if (treeLoading) return <LoadingState />;
  // Loaded but nothing to browse: say so, instead of spinning forever
  // waiting for a specialty that will never be picked.
  if (treeError || specialties.length === 0) {
    return (
      <Screen>
        <ScreenChrome title={t("guidelinesLabel")} onBack={goBack} />
        <LoadFailed message={t("medscapeTreeUnavailable")} onRetry={() => refetchTree()} busy={treeFetching} />
      </Screen>
    );
  }
  if (!specialty) return <LoadingState />;

  return (
    <Screen scroll={false} padded={false}>
      <View style={{ flex: 1, padding: layout.screenPadding, paddingBottom: 0 }}>
        <ScreenChrome
          title={t("guidelinesLabel")}
          onBack={goBack}
          tour="guidelines"
          actions={
            <FavoritesChip
              kind="guideline"
              open={favoritesOpen}
              onToggle={() => setFavoritesOpen((open) => !open)}
            />
          }
        />

        {favoritesOpen ? (
          <ScrollView style={{ maxHeight: 180, flexGrow: 0, marginBottom: spacing.sm }}>
            <ReferenceFavorites kind="guideline" />
          </ScrollView>
        ) : null}

        <TourTarget id="guide.search" style={{ marginBottom: spacing.md }}>
          <BrowseSearch
            value={q}
            onChangeText={setQ}
            placeholder={t("medscapeSearchInSpecialty")}
          />
        </TourTarget>

        <TourTarget id="guide.specialties" style={{ marginBottom: spacing.md }}>
          <TopicRail
            topics={specialties}
            active={specialty}
            onSelect={setActiveSpecialty}
            label={t("browseTopics")}
          />
        </TourTarget>

        <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <AppText
            muted
            weight="800"
            size={11}
            style={{ letterSpacing: 0.4, textAlign: "left", writingDirection: "ltr", flex: 1 }}
          >
            {query.length === 0 ? t("medscapeAllArticlesAZ") : `${n(filtered.length)} ${t("medscapeArticleCount")}`}
          </AppText>
          {(recent?.length ?? 0) > 0 ? (
            <Pressable
              onPress={() => setShowRecent((open) => !open)}
              accessibilityRole="button"
              accessibilityState={{ selected: showRecent }}
              hitSlop={6}
              style={{
                flexDirection: "row",
                alignItems: "center",
                gap: 5,
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: 999,
                backgroundColor: showRecent ? colors.accent : colors.cardBg,
                boxShadow: showRecent ? undefined : colors.cardShadow,
              }}
            >
              <AppText size={10} color={showRecent ? colors.onAccent : colors.muted}>◷</AppText>
              <AppText weight="800" size={10.5} color={showRecent ? colors.onAccent : colors.muted}>
                {t("browseNew")}
              </AppText>
            </Pressable>
          ) : null}
        </View>

        {itemsLoading ? (
          <LoadingState />
        ) : (
          <View style={{ flex: 1, minHeight: 0 }}>
            {showRecent && (recent?.length ?? 0) > 0 ? (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={{ flexGrow: 0, marginBottom: 10 }}
                contentContainerStyle={{ gap: 10 }}
              >
                {(recent ?? []).map((a) => (
                  <RecentCard key={a.slug} article={a} onPress={() => openArticle(a.slug)} />
                ))}
              </ScrollView>
            ) : null}

            <TourTarget id="guide.list" style={{ flex: 1, minHeight: 0 }}>
              <AlphabeticalArticleList items={filtered} onPressItem={openArticle} emptyText={t("medscapeNoLocalResults")} />
            </TourTarget>
          </View>
        )}
      </View>
    </Screen>
  );
}

function RecentCard({ article, onPress }: { article: MedscapeArticleListItem; onPress: () => void }) {
  const { colors } = useTheme();
  return (
    <Pressable onPress={onPress} style={{ width: 168 }}>
      <View
        style={{
          backgroundColor: colors.cardBg,
          boxShadow: colors.cardShadow,
          borderRadius: 14,
          padding: 12,
          height: 96,
        }}
      >
        {article.latest_update ? (
          <View
            style={{
              alignSelf: "flex-start",
              backgroundColor: colors.accent,
              borderRadius: 999,
              paddingHorizontal: 8,
              paddingVertical: 3,
              marginBottom: 8,
            }}
          >
            <AppText weight="800" size={9.5} color={colors.onAccent}>
              {formatMonthYear(article.latest_update)}
            </AppText>
          </View>
        ) : null}
        <AppText
          weight="700"
          size={12.5}
          numberOfLines={2}
          style={{ lineHeight: 17, textAlign: "left", writingDirection: "ltr" }}
        >
          {article.title}
        </AppText>
      </View>
    </Pressable>
  );
}
