import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem, MedscapeKind } from "@/api/types";
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
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";

/** Shared by the "guidelines" and "diseasesConditions" screens -- same
 * backend (apps.medscape), same browse-by-category UX, kind is just which
 * one the current screen is. There are ~3200 disease articles, too many to
 * fetch as one list and group client-side (the calculators approach), so
 * the tree (category -> specialty -> count) loads up front and a
 * specialty's articles load lazily only once that row is opened. */
export function MedscapeBrowseScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const screen = useNav((s) => s.screen);
  const kind: MedscapeKind = screen === "guidelines" ? "guideline" : "disease";
  const titleKey: StringKey = screen === "guidelines" ? "guidelinesLabel" : "diseasesConditionsLabel";

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const [openCategory, setOpenCategory] = useState<string | null>(null);
  const [openSpecialty, setOpenSpecialty] = useState<string | null>(null);

  const { data: tree, isLoading } = useQuery({
    queryKey: ["medscape-tree", kind],
    queryFn: () => medscapeApi.tree(kind),
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ["medscape-search", kind, query],
    queryFn: () => medscapeApi.search(kind, query),
    enabled: query.length >= 2,
  });

  const openArticle = (slug: string) => navigate("medscapeArticle", { slug });

  if (isLoading) return <LoadingState />;

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
        <View style={{ gap: 8 }}>
          {(tree ?? []).map((node) => (
            <View
              key={node.category}
              style={{
                backgroundColor: colors.cardBg,
                borderRadius: 14,
                borderWidth: 1,
                borderColor: colors.border,
                overflow: "hidden",
              }}
            >
              <Pressable
                onPress={() => {
                  setOpenCategory(openCategory === node.category ? null : node.category);
                  setOpenSpecialty(null);
                }}
                style={{ padding: 13, flexDirection: row, alignItems: "center", justifyContent: "space-between" }}
              >
                <AppText weight="800" size={13}>
                  {node.category.charAt(0).toUpperCase() + node.category.slice(1)}
                </AppText>
                <AppText muted weight="700" size={12}>
                  {node.specialties.reduce((a, s) => a + s.count, 0)} {openCategory === node.category ? "▲" : "▼"}
                </AppText>
              </Pressable>

              {openCategory === node.category ? (
                <View style={{ paddingHorizontal: 10, paddingBottom: 10, gap: 6 }}>
                  {node.specialties.map((sp) => (
                    <View
                      key={sp.name}
                      style={{
                        backgroundColor: colors.softBg,
                        borderRadius: 12,
                        borderWidth: 1,
                        borderColor: colors.trackBg,
                        overflow: "hidden",
                      }}
                    >
                      <Pressable
                        onPress={() => setOpenSpecialty(openSpecialty === sp.name ? null : sp.name)}
                        style={{ padding: 11, flexDirection: row, alignItems: "center", justifyContent: "space-between" }}
                      >
                        <AppText weight="700" size={12.5}>
                          {sp.name}
                        </AppText>
                        <AppText muted weight="700" size={11.5}>
                          {sp.count} {openSpecialty === sp.name ? "▲" : "▼"}
                        </AppText>
                      </Pressable>
                      {openSpecialty === sp.name ? (
                        <SpecialtyArticles
                          kind={kind}
                          category={node.category}
                          specialty={sp.name}
                          onPick={openArticle}
                        />
                      ) : null}
                    </View>
                  ))}
                </View>
              ) : null}
            </View>
          ))}
        </View>
      )}
    </Screen>
  );
}

function SpecialtyArticles({
  kind,
  category,
  specialty,
  onPick,
}: {
  kind: MedscapeKind;
  category: string;
  specialty: string;
  onPick: (slug: string) => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["medscape-articles", kind, category, specialty],
    queryFn: () => medscapeApi.bySpecialty(kind, category, specialty),
  });

  return (
    <View style={{ paddingHorizontal: 8, paddingBottom: 8, gap: 6 }}>
      {isLoading ? (
        <AppText muted size={12} style={{ paddingVertical: 6 }}>
          …
        </AppText>
      ) : (
        (data ?? []).map((a) => <ArticleRow key={a.slug} article={a} onPress={() => onPick(a.slug)} />)
      )}
    </View>
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
