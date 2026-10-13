import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { uptodateApi } from "@/api/endpoints";
import { countWords, readingMinutes } from "@/components/article/numbering";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useReader } from "@/store/reader";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";
import { stripHtml } from "@/utils/html";
import { numberedOutline, outlineTops, shortDate } from "@/utils/uptodateOutline";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };

// UpToDate sets its top-level headings in capitals; those read lighter.
const isAllCaps = (title: string) => /[A-Z]/.test(title) && title === title.toUpperCase();

/** An UpToDate topic's home page (design option 1), shown after picking a
 * search result: section, title and the topic's version/date/reading time
 * on a white header, a button into the reader (picking up where it was left)
 * plus one that opens it with in-article search, then the numbered table of
 * contents. UpToDate's content is English-only, so the article's own text
 * is laid out left to right whatever the app's language. */
export function UptodateOutlineScreen() {
  const { t, n, row, isFa } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const id = String(useNav((s) => s.params.id ?? ""));
  const titleParam = String(useNav((s) => s.params.title ?? ""));
  const lastIndex = useReader((s) => s.lastSection[`utd:${id}`]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id],
    queryFn: () => uptodateApi.topic(id),
    enabled: !!id,
  });

  const tops = useMemo(() => outlineTops(numberedOutline(data?.outline_html ?? "")), [data]);
  const minutes = useMemo(() => (data ? readingMinutes(countWords(stripHtml(data.body_html))) : 0), [data]);
  const lastTop = lastIndex !== undefined && lastIndex > 0 ? tops[lastIndex] : undefined;
  const [expanded, setExpanded] = useState<string | null>(null);
  const openId = expanded ?? lastTop?.id ?? null;
  const title = data?.title || titleParam;

  const read = (sectionId?: string, openSearch?: boolean) =>
    navigate("uptodateArticle", { id, title, sectionId, openSearch });

  const version = data?.version ? `v${data.version.replace(/\.0+$/, "")}` : "";
  const chips = [version, data?.updated ? shortDate(data.updated) : "", minutes ? `${minutes} min read` : ""].filter(Boolean);

  return (
    <View style={{ flex: 1, backgroundColor: colors.softBg }}>
      <View style={{ backgroundColor: colors.cardBg, paddingHorizontal: 20, paddingTop: 18, paddingBottom: 20, gap: 12 }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <ChromeButton onPress={goBack} size={34}>
            <AppText weight="800" size={16} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <LangToggleButton />
        </View>

        <View style={{ gap: 8 }}>
          {data?.section ? (
            <AppText weight="800" size={11} color={colors.accent} style={[LTR, { letterSpacing: 1.2, lineHeight: 16 }]}>
              {data.section.toUpperCase()} · TOPIC
            </AppText>
          ) : null}
          <AppText weight="900" size={22} style={[LTR, { lineHeight: 30 }]}>
            {title}
          </AppText>
          {chips.length ? (
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
              {chips.map((chip) => (
                <View key={chip} style={{ backgroundColor: colors.softBg, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 }}>
                  <AppText weight="700" size={11.5} style={[LTR, { lineHeight: 16 }]}>
                    {chip}
                  </AppText>
                </View>
              ))}
            </View>
          ) : null}
        </View>

        {data ? (
          <View style={{ flexDirection: row, gap: 10, marginTop: 4 }}>
            <Pressable
              onPress={() => read(lastTop?.id)}
              style={{ flex: 1, height: 46, borderRadius: 14, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" }}
            >
              <AppText weight="800" size={14} color={colors.onAccent}>
                {lastTop?.num ? `${t("articleContinueFrom")} ${n(lastTop.num)}` : t("articleStartReading")}
              </AppText>
            </Pressable>
            <Pressable
              onPress={() => read(undefined, true)}
              accessibilityLabel={t("uptodateSearchInArticleHint")}
              style={{
                width: 46,
                height: 46,
                borderRadius: 14,
                borderWidth: 1,
                borderColor: colors.trackBg,
                backgroundColor: colors.cardBg,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AppText weight="800" size={18} color={colors.accent} style={{ lineHeight: 22 }}>
                ⌕
              </AppText>
            </Pressable>
          </View>
        ) : null}
      </View>

      {isLoading ? (
        <LoadingState />
      ) : isError || !data ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
          <AppText muted weight="600">
            {t("articleLoadError")}
          </AppText>
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, gap: 8, paddingBottom: layout.bottomNavHeight + 24 }}>
          <AppText weight="800" size={13} muted>
            {t("articleContents")}
          </AppText>
          {tops.length === 0 ? (
            <AppText muted weight="600" size={13} center style={{ marginTop: 20 }}>
              {t("uptodateOutlineEmpty")}
            </AppText>
          ) : (
            <View style={{ backgroundColor: colors.cardBg, borderRadius: 16, overflow: "hidden" }}>
              {tops.map((top, i) => {
                const open = openId === top.id && top.children.length > 0;
                return (
                  <View
                    key={top.id}
                    style={{
                      borderTopWidth: i === 0 ? 0 : 1,
                      borderTopColor: colors.sheetLine,
                      backgroundColor: open ? colors.softBg : undefined,
                    }}
                  >
                    <View style={{ flexDirection: "row", alignItems: "center" }}>
                      <Pressable
                        onPress={() => read(top.id)}
                        style={{ flex: 1, flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 13, paddingLeft: 14 }}
                      >
                        <View
                          style={{
                            width: 26,
                            height: 26,
                            borderRadius: 8,
                            backgroundColor: open ? colors.accent : `${colors.accent}1A`,
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <AppText weight="800" size={top.num && top.num.length > 1 ? 11 : 12} color={open ? colors.onAccent : colors.accent} center style={{ lineHeight: 16 }}>
                            {top.num ?? "·"}
                          </AppText>
                        </View>
                        <AppText
                          weight={open ? "800" : isAllCaps(top.title) ? "600" : "700"}
                          size={isAllCaps(top.title) ? 13 : 14}
                          color={open ? colors.accent : colors.ink}
                          style={[LTR, { flex: 1, lineHeight: 20, letterSpacing: isAllCaps(top.title) ? 0.3 : 0 }]}
                        >
                          {top.title}
                        </AppText>
                      </Pressable>
                      {top.children.length > 0 ? (
                        <Pressable
                          onPress={() => setExpanded(open ? "" : top.id)}
                          hitSlop={6}
                          accessibilityLabel="expand"
                          style={{ width: 42, alignItems: "center", paddingVertical: 13 }}
                        >
                          <AppText weight="800" size={12} color={open ? colors.accent : colors.muted}>
                            {open ? "▴" : "▾"}
                          </AppText>
                        </Pressable>
                      ) : (
                        <View style={{ width: 42 }} />
                      )}
                    </View>
                    {open ? (
                      <View style={{ paddingLeft: 52, paddingRight: 14, paddingBottom: 10, gap: 2 }}>
                        {top.children.map((child) => (
                          <Pressable key={child.id} onPress={() => read(child.id)} style={{ paddingVertical: 5 }}>
                            <AppText weight="600" size={13} color={colors.proseInk} style={[LTR, { lineHeight: 19 }]}>
                              {child.num ? `${child.num}  ` : ""}
                              {child.title}
                            </AppText>
                          </Pressable>
                        ))}
                      </View>
                    ) : null}
                  </View>
                );
              })}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}
