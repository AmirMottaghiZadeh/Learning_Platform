import { useQuery } from "@tanstack/react-query";
import React, { useMemo } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { uptodateApi } from "@/api/endpoints";
import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { parseOutline } from "@/utils/uptodateOutline";

/** Shown after picking a search result and before the full article loads: a
 * plain list of the article's headings/subheadings (parsed from
 * `outline_html`, matching the real UpToDate app's topic outline). Tapping
 * one opens the article scrolled straight to that heading. */
export function UptodateOutlineScreen() {
  const { t, isFa, row } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const id = String(useNav((s) => s.params.id ?? ""));
  const titleParam = String(useNav((s) => s.params.title ?? ""));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id],
    queryFn: () => uptodateApi.topic(id),
    enabled: !!id,
  });

  const outline = useMemo(() => parseOutline(data?.outline_html ?? ""), [data]);
  const title = data?.title || titleParam;

  const openArticle = (sectionId?: string) =>
    navigate("uptodateArticle", { id, title, sectionId });

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View
        style={{
          flexDirection: row,
          alignItems: "center",
          gap: 10,
          paddingHorizontal: 18,
          paddingTop: 16,
          paddingBottom: 12,
          borderBottomWidth: 1,
          borderBottomColor: colors.sheetLine,
        }}
      >
        <ChromeButton onPress={goBack} size={30}>
          <AppText weight="800" size={15} color={colors.ink}>
            {isFa ? "›" : "‹"}
          </AppText>
        </ChromeButton>
        <AppText weight="800" size={14} numberOfLines={2} style={{ flex: 1 }}>
          {title}
        </AppText>
      </View>

      {isLoading ? (
        <LoadingState />
      ) : isError || !data ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
          <AppText muted weight="600">
            {isFa ? "بارگذاری مقاله ممکن نشد." : "Could not load the article."}
          </AppText>
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 18, paddingBottom: 40 }}>
          <Pressable
            onPress={() => openArticle()}
            style={[
              {
                backgroundColor: colors.accent,
                borderRadius: 14,
                paddingVertical: 14,
                alignItems: "center",
                marginBottom: 18,
              },
              shadows.raisedSm,
            ]}
          >
            <AppText weight="800" size={14} color={colors.onAccent}>
              {t("uptodateViewFullArticle")}
            </AppText>
          </Pressable>

          {outline.length === 0 ? (
            <AppText muted weight="600" size={13} center style={{ marginTop: 20 }}>
              {t("uptodateOutlineEmpty")}
            </AppText>
          ) : (
            <>
              <AppText muted weight="600" size={12} style={{ marginBottom: 10 }}>
                {t("uptodateOutlineHint")}
              </AppText>
              <View style={{ gap: 2 }}>
                {outline.map((node, i) => (
                  <Pressable
                    key={`${node.id}-${i}`}
                    onPress={() => openArticle(node.id)}
                    style={{
                      paddingVertical: 11,
                      borderBottomWidth: 1,
                      borderBottomColor: colors.sheetLine,
                      ...(isFa
                        ? { paddingRight: 14 + node.depth * 18 }
                        : { paddingLeft: 14 + node.depth * 18 }),
                    }}
                  >
                    <AppText
                      weight={node.depth === 0 ? "800" : "600"}
                      size={node.depth === 0 ? 14 : 13}
                      color={node.depth === 0 ? colors.ink : colors.muted}
                    >
                      {node.title}
                    </AppText>
                  </Pressable>
                ))}
              </View>
            </>
          )}
        </ScrollView>
      )}
    </View>
  );
}
