import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Pressable, ScrollView, TextInput, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem } from "@/api/types";
import { AlphabeticalArticleList } from "@/components/AlphabeticalArticleList";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout, spacing } from "@/theme/tokens";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatMonthYear(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/** Guidelines have no specialty taxonomy the way diseases do -- the source
 * gives three flat content-type buckets (Guidelines/Expert Insights/Primary
 * Care Hacks) with no secondary grouping, so the disease browse screen's
 * category-tabs-over-a-specialty-grid doesn't apply here. This screen goes
 * straight from type tabs to one flat A-Z list, with a "Recently Updated"
 * spotlight above it -- the one genuine freshness signal this source gives
 * (about a quarter of guideline-bucket articles carry a dated change-log
 * section), which matters more for guidelines than alphabetical browsing
 * alone. Absent for the other two buckets, which have no such section. */
export function MedscapeGuidelinesScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [activeSpecialty, setActiveSpecialty] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const { data: tree, isLoading: treeLoading } = useQuery({
    queryKey: ["medscape-tree", "guideline"],
    queryFn: () => medscapeApi.tree("guideline"),
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

  const openArticle = (slug: string) => navigate("medscapeArticle", { slug });

  if (treeLoading || !specialty) return <LoadingState />;

  return (
    <Screen scroll={false} padded={false}>
      <View style={{ flex: 1, padding: layout.screenPadding, paddingBottom: 0 }}>
        <ScreenChrome title={t("guidelinesLabel")} onBack={goBack} />

        {specialties.length > 1 ? (
          <View
            style={{
              flexDirection: row,
              backgroundColor: colors.pageBg,
              borderRadius: 12,
              padding: 3,
              marginBottom: spacing.md,
            }}
          >
            {specialties.map((sp) => {
              const active = sp.name === specialty;
              return (
                <Pressable key={sp.name} onPress={() => setActiveSpecialty(sp.name)} style={{ flex: 1 }}>
                  <View
                    style={{
                      alignItems: "center",
                      paddingVertical: 8,
                      borderRadius: 9,
                      backgroundColor: active ? colors.accent : "transparent",
                    }}
                  >
                    <AppText weight={active ? "800" : "700"} size={11.5} color={active ? colors.onAccent : colors.muted}>
                      {sp.name}
                    </AppText>
                  </View>
                </Pressable>
              );
            })}
          </View>
        ) : null}

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
            marginBottom: spacing.md,
          }}
        >
          <AppText muted>⌕</AppText>
          <TextInput
            value={q}
            onChangeText={setQ}
            placeholder={t("medscapeSearchInSpecialty")}
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
        </View>

        {itemsLoading ? (
          <LoadingState />
        ) : (
          <View style={{ flex: 1, minHeight: 0 }}>
            {query.length === 0 && (recent?.length ?? 0) > 0 ? (
              <>
                <AppText weight="800" size={13} style={{ marginBottom: 10, textAlign: "left", writingDirection: "ltr" }}>
                  {t("medscapeRecentlyUpdated")}
                </AppText>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  style={{ flexGrow: 0, marginBottom: 16 }}
                  contentContainerStyle={{ gap: 10 }}
                >
                  {(recent ?? []).map((a) => (
                    <RecentCard key={a.slug} article={a} onPress={() => openArticle(a.slug)} />
                  ))}
                </ScrollView>
                <View style={{ height: 1, backgroundColor: colors.trackBg, marginBottom: 10 }} />
              </>
            ) : null}

            <AppText
              muted
              weight="800"
              size={11}
              style={{ marginBottom: 6, letterSpacing: 0.4, textAlign: "left", writingDirection: "ltr" }}
            >
              {query.length === 0 ? t("medscapeAllArticlesAZ") : `${filtered.length} ${t("medscapeArticleCount")}`}
            </AppText>

            <AlphabeticalArticleList items={filtered} onPressItem={openArticle} emptyText={t("medscapeNoLocalResults")} />
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
          borderWidth: 1,
          borderColor: colors.border,
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
