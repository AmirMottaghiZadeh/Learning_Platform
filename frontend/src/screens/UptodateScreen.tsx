import { useInfiniteQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { NativeScrollEvent, NativeSyntheticEvent, Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { ApiError } from "@/api/client";
import { UptodateSearchResult } from "@/api/types";
import { ChromeButton, LangToggleButton, TourButton } from "@/components/ScreenChrome";
import { OfflineDownloadButton } from "@/components/offline/OfflineDownloadButton";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { uptodateSource } from "@/offline/sources";
import { FavoriteArticle, useLibrary } from "@/store/library";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { fontFamily } from "@/theme/fonts";
import { shortDate } from "@/utils/uptodateOutline";
import { useNavClearance } from "@/components/BottomNav";
import { useBleedTop } from "@/components/AppShell";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };
// The busiest sections among the results get a filter chip; the rest are
// still under "All".
const MAX_SECTION_CHIPS = 4;
// Results per page; the next page loads as the list nears its end.
const PAGE = 30;

// some titles italicise a name: "<i>Chlamydia pneumoniae</i>"
const TAG_RE = /<[^>]*>/g;

/** UpToDate search (design option 1): a white header with the search field
 * and one chip per clinical section among the results, then a card per
 * topic with its section, title, a snippet around the hit and its date. */
export function UptodateScreen() {
  const navClearance = useNavClearance();
  const { t, n, row, isFa } = useLang();
  const { colors, shadows } = useTheme();
  const bleedTop = useBleedTop(true);
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const [section, setSection] = useState<string | null>(null);
  const favorites = useLibrary((s) => s.favorites);
  // a new query starts on "All"
  React.useEffect(() => setSection(null), [query]);

  // Every title with the words is a result: one page at a time, the next
  // as the list nears its end. Counts and section chips cover all of them.
  const { data, isFetching, error, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ["uptodate-search-page", query, section ?? ""],
    queryFn: ({ pageParam }) => uptodateSource.searchPage(query, { limit: PAGE, offset: pageParam, section: section ?? "" }),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.results.length, 0);
      return last.results.length && loaded < last.total ? loaded : undefined;
    },
    enabled: query.length >= 2,
    retry: false,
  });

  const locked = error instanceof ApiError && error.status === 503;
  const first = data?.pages[0];
  const rows = useMemo(() => data?.pages.flatMap((page) => page.results) ?? [], [data]);
  const sections = useMemo(() => (first?.sections ?? []).map((s) => [s.name, s.count] as const), [first]);
  const activeSection = section && sections.some(([s]) => s === section) ? section : null;
  const total = first?.total ?? 0;
  // the query as searched, when a misspelt word was corrected
  const corrected = first?.corrected ?? "";
  const loadMore = () => {
    if (hasNextPage && !isFetchingNextPage) void fetchNextPage();
  };
  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { layoutMeasurement, contentOffset, contentSize } = e.nativeEvent;
    if (layoutMeasurement.height + contentOffset.y >= contentSize.height - 600) loadMore();
  };
  useTour("uptodate", true);

  return (
    <View style={{ flex: 1, backgroundColor: colors.softBg }}>
      <View
        style={{
          backgroundColor: colors.cardBg,
          paddingHorizontal: 20,
          paddingTop: 18 + bleedTop,
          paddingBottom: 14,
          borderBottomWidth: 1,
          borderBottomColor: colors.trackBg,
          gap: 14,
        }}
      >
        <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
          <ChromeButton onPress={goBack} size={34}>
            <AppText weight="800" size={16} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <AppText weight="900" size={18} style={{ flex: 1 }}>
            {t("uptodateScreenTitle")}
          </AppText>
          <TourButton tour="uptodate" size={34} />
          <OfflineDownloadButton dataset="uptodate" tourId="utd.offline" />
          <LangToggleButton />
        </View>

        <TourTarget id="utd.search">
        <View
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 10,
            backgroundColor: colors.inputBg,
            borderWidth: 2,
            borderColor: colors.accent,
            borderRadius: 14,
            paddingHorizontal: 14,
            paddingVertical: 9,
          }}
        >
          <AppText weight="800" size={17} color={colors.accent} style={{ lineHeight: 22 }}>
            ⌕
          </AppText>
          <TextInput
            value={q}
            onChangeText={setQ}
            placeholder={t("uptodateSearchPlaceholder")}
            placeholderTextColor={colors.muted}
            autoCorrect={false}
            autoCapitalize="none"
            style={{
              flex: 1,
              // lets the field shrink below a browser input's built-in width,
              // so the clear button stays inside the box on a narrow phone
              minWidth: 0,
              fontFamily: fontFamily("600"),
              fontSize: 15,
              color: colors.ink,
              textAlign: q ? "left" : isFa ? "right" : "left",
              writingDirection: q ? "ltr" : undefined,
              padding: 0,
              // the field's own 2px accent border is the focus state
              ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as object) : null),
            }}
          />
          {isFetching ? (
            <AppText muted size={12}>
              …
            </AppText>
          ) : q ? (
            <Pressable onPress={() => setQ("")} hitSlop={10} accessibilityLabel="clear">
              <AppText muted weight="700" size={18} style={{ lineHeight: 22 }}>
                ×
              </AppText>
            </Pressable>
          ) : null}
        </View>
        </TourTarget>

        {sections.length > 1 ? (
          <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
            <Chip label={`${t("articleSearchAll")} · ${n(first?.all ?? total)}`} on={!activeSection} onPress={() => setSection(null)} />
            {sections.slice(0, MAX_SECTION_CHIPS).map(([name, count]) => (
              <Chip key={name} label={name} count={n(count)} on={activeSection === name} onPress={() => setSection(name)} />
            ))}
          </View>
        ) : null}
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, gap: 10, paddingBottom: navClearance + 24 }}
        onScroll={onScroll}
        scrollEventThrottle={200}
        keyboardShouldPersistTaps="handled"
      >
        {locked ? (
          <View style={{ backgroundColor: colors.cardBg, borderRadius: 16, padding: 16 }}>
            <AppText weight="800" size={15} color={colors.accent}>
              {t("comingSoon")}
            </AppText>
            <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
              {t("lockedFeature")}
            </AppText>
          </View>
        ) : query.length >= 2 && rows.length === 0 && !isFetching ? (
          <View style={{ alignItems: "center", paddingVertical: 40 }}>
            <View
              style={{
                width: 60,
                height: 60,
                borderRadius: 18,
                backgroundColor: colors.cardBg,
                borderWidth: 1,
                borderColor: colors.trackBg,
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 14,
              }}
            >
              <IconImage name="entry-diseases" size={34} />
            </View>
            <AppText weight="800" size={15}>
              {t("uptodateEmptyTitle")}
            </AppText>
            <AppText muted weight="600" size={13} center style={{ marginTop: 8, lineHeight: 22 }}>
              {t("uptodateEmptySub")}
            </AppText>
          </View>
        ) : query.length < 2 ? (
          <Favorites items={favorites} onOpen={(f) => navigate("uptodateOutline", { id: f.id, title: f.title })} />
        ) : (
          <>
            {corrected ? (
              <View style={{ flexDirection: row, flexWrap: "wrap", alignItems: "center", gap: 5 }}>
                <AppText weight="600" size={12.5} muted>
                  {t("uptodateCorrected")}
                </AppText>
                <AppText weight="800" size={12.5} color={colors.accent} style={LTR}>
                  {corrected}
                </AppText>
              </View>
            ) : null}
            {query.length >= 2 && total > 0 ? (
              <AppText weight="700" size={12} muted>
                {t("uptodateResultCount").replace("{n}", n(total))}
              </AppText>
            ) : null}
            {rows.map((r) => (
              <ResultCard
                key={r.id}
                result={r}
                onPress={() => navigate("uptodateOutline", { id: r.id, title: r.title.replace(TAG_RE, "") })}
                shadow={shadows.raisedSm}
              />
            ))}
            {hasNextPage ? (
              <Pressable
                onPress={loadMore}
                disabled={isFetchingNextPage}
                style={{ alignSelf: "center", paddingHorizontal: 18, paddingVertical: 10, borderRadius: 999, backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.trackBg }}
              >
                <AppText weight="800" size={13} color={colors.accent}>
                  {isFetchingNextPage
                    ? "…"
                    : t("uptodateMoreResults").replace("{n}", n(Math.max(0, total - rows.length)))}
                </AppText>
              </Pressable>
            ) : null}
          </>
        )}
      </ScrollView>
    </View>
  );
}

/** A filter pill. A section chip (`count` given) keeps its count in view and
 * cuts the end of a long English section name ("Emergency Medicine (Adult
 * and Pediatric)") short on a narrow phone, instead of running off screen. */
function Chip({ label, count, on, onPress }: { label: string; count?: string; on: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  const textProps = { weight: on ? ("800" as const) : ("700" as const), size: 12, color: on ? colors.onAccent : colors.ink };
  return (
    <Pressable
      onPress={onPress}
      style={{
        maxWidth: "100%",
        flexDirection: "row",
        paddingHorizontal: 12,
        paddingVertical: 5,
        borderRadius: 999,
        backgroundColor: on ? colors.accent : colors.softBg,
        borderWidth: 1,
        borderColor: on ? colors.accent : colors.trackBg,
      }}
    >
      {count === undefined ? (
        <AppText {...textProps} numberOfLines={1} style={{ lineHeight: 18 }}>
          {label}
        </AppText>
      ) : (
        <>
          <AppText {...textProps} numberOfLines={1} style={[LTR, { lineHeight: 18, flexShrink: 1 }]}>
            {label}
          </AppText>
          <AppText {...textProps} numberOfLines={1} style={[LTR, { lineHeight: 18, flexShrink: 0, marginLeft: 4 }]}>
            {`· ${count}`}
          </AppText>
        </>
      )}
    </Pressable>
  );
}

function ResultCard({ result, onPress, shadow }: { result: UptodateSearchResult; onPress: () => void; shadow: object }) {
  const { colors } = useTheme();
  // the start of each title word the query matched, highlighted
  const title = useMemo(() => {
    const text = result.title.replace(TAG_RE, "");
    const terms = result.terms ?? [];
    if (!terms.length) return text;
    const parts: React.ReactNode[] = [];
    let at = 0;
    for (const word of text.matchAll(/[A-Za-z0-9]+/g)) {
      const lower = word[0].toLowerCase();
      // the longest term at the word's start, else the first one inside it
      const start = Math.max(0, ...terms.filter((t) => lower.startsWith(t)).map((t) => t.length));
      const inner = start ? null : terms.find((t) => t.length >= 4 && lower.includes(t));
      const from = start ? 0 : inner ? lower.indexOf(inner) : -1;
      const length = start || inner?.length || 0;
      if (from < 0 || !length) continue;
      const begin = word.index! + from;
      parts.push(text.slice(at, begin));
      parts.push(
        <Text key={begin} style={{ backgroundColor: `${colors.accent}2E`, color: colors.ink, borderRadius: 3 }}>
          {text.slice(begin, begin + length)}
        </Text>,
      );
      at = begin + length;
    }
    parts.push(text.slice(at));
    return parts;
  }, [result.title, result.terms, colors]);

  return (
    <Pressable
      onPress={onPress}
      style={[{ backgroundColor: colors.cardBg, borderRadius: 16, paddingVertical: 14, paddingHorizontal: 16, gap: 5 }, shadow]}
    >
      {result.section ? (
        <AppText weight="800" size={10.5} color={colors.accent} style={[LTR, { letterSpacing: 1, lineHeight: 15 }]}>
          {result.section.toUpperCase()}
        </AppText>
      ) : null}
      <AppText weight="800" size={15} style={[LTR, { lineHeight: 21 }]}>
        {title}
      </AppText>
      {result.updated ? (
        <AppText weight="600" size={11} muted style={[LTR, { lineHeight: 16, opacity: 0.85 }]}>
          Updated {shortDate(result.updated)}
        </AppText>
      ) : null}
    </Pressable>
  );
}

/** The articles the learner starred, newest first: what the screen shows
 * before anything is searched. */
function Favorites({ items, onOpen }: { items: FavoriteArticle[]; onOpen: (f: FavoriteArticle) => void }) {
  const { t, row } = useLang();
  const { colors, shadows } = useTheme();
  const toggleFavorite = useLibrary((s) => s.toggleFavorite);
  const mine = items.filter((f) => f.source === "utd");
  return (
    <View style={{ gap: 10 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
        <AppText weight="900" size={15} color="#E0A526">
          ★
        </AppText>
        <AppText weight="800" size={14}>
          {t("favoritesTitle")}
        </AppText>
      </View>
      {mine.length === 0 ? (
        <View style={{ backgroundColor: colors.cardBg, borderRadius: 16, padding: 16 }}>
          <AppText weight="600" size={13} muted style={{ lineHeight: 22 }}>
            {t("favoritesEmpty")}
          </AppText>
        </View>
      ) : (
        mine.map((f) => (
          <Pressable
            key={f.id}
            onPress={() => onOpen(f)}
            style={[{ flexDirection: "row", alignItems: "center", gap: 10, backgroundColor: colors.cardBg, borderRadius: 16, paddingVertical: 12, paddingLeft: 16, paddingRight: 8 }, shadows.raisedSm]}
          >
            <View style={{ flex: 1, gap: 4 }}>
              {f.section ? (
                <AppText weight="800" size={10.5} color={colors.accent} style={[LTR, { letterSpacing: 1, lineHeight: 15 }]}>
                  {f.section.toUpperCase()}
                </AppText>
              ) : null}
              <AppText weight="800" size={14.5} style={[LTR, { lineHeight: 20 }]}>
                {f.title}
              </AppText>
            </View>
            <Pressable
              onPress={() => toggleFavorite(f)}
              hitSlop={8}
              accessibilityLabel={t("favoriteRemove")}
              style={{ width: 40, height: 40, alignItems: "center", justifyContent: "center" }}
            >
              <AppText weight="800" size={18} color="#E0A526">
                ★
              </AppText>
            </Pressable>
          </Pressable>
        ))
      )}
    </View>
  );
}
