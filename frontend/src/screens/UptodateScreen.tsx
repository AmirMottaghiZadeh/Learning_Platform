import { useInfiniteQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Keyboard, NativeScrollEvent, NativeSyntheticEvent, Platform, Pressable, ScrollView, Text, TextInput, useWindowDimensions, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { ApiError } from "@/api/client";
import { UptodateSearchResult, UptodateSearchSuggestion } from "@/api/types";
import { SuggestionFilter, UptodateSuggestionMenu } from "@/components/UptodateSuggestionMenu";
import { ChromeButton, LangToggleButton, TourButton } from "@/components/ScreenChrome";
import { OfflineDownloadButton } from "@/components/offline/OfflineDownloadButton";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { uptodateSource } from "@/offline/sources";
import { suggestionKind } from "@/offline/uptodateSearchCatalog";
import { useBackInterceptor } from "@/navigation/back";
import { FavoriteArticle, useLibrary } from "@/store/library";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { fontFamily } from "@/theme/fonts";
import { shortDate } from "@/utils/uptodateOutline";
import { useNavClearance } from "@/components/BottomNav";
import { useBleedTop } from "@/components/AppShell";
import { stripHtml } from "@/utils/html";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };
// Results per page; the next page loads as the list nears its end.
const PAGE = 30;


/** UpToDate search with the selected guided dropdown and specialty filters. */
export function UptodateScreen() {
  const navClearance = useNavClearance();
  const { t, n, row, isFa } = useLang();
  const { colors, shadows } = useTheme();
  const bleedTop = useBleedTop(true);
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim(), 200);
  const [section, setSection] = useState<string | null>(null);
  const sectionScroll = React.useRef<ScrollView>(null);
  const rootRef = React.useRef<View>(null);
  const fieldRef = React.useRef<View>(null);
  const inputRef = React.useRef<TextInput>(null);
  const keyboardTop = React.useRef(Infinity);
  const blurTimer = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const dimensions = useWindowDimensions();
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [suggestionFilter, setSuggestionFilter] = useState<SuggestionFilter>("all");
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 20, width: 0, maxHeight: 380 });
  const menuVisible = suggestionsOpen && q.trim().length > 0;
  const dismissSuggestions = () => { setSuggestionsOpen(false); setActiveSuggestion(-1); Keyboard.dismiss(); };
  useBackInterceptor(menuVisible, dismissSuggestions);
  const measureMenu = React.useCallback(() => {
    if (!rootRef.current) return;
    // Measure relative to one ancestor, so an in-flight screen transition
    // cannot shift the two window measurements between callbacks.
    fieldRef.current?.measureLayout(rootRef.current, (left, top, width, height) => {
      rootRef.current?.measureInWindow((_rootX, rootY, _rootWidth, rootHeight) => {
        const visibleBottom = Platform.OS === "web" && window.visualViewport
          ? window.visualViewport.height + window.visualViewport.offsetTop : Infinity;
        setMenuPosition({ top: top + height + 8, left, width,
          maxHeight: Math.max(120, Math.min(400, Math.min(rootY + rootHeight - navClearance, keyboardTop.current, visibleBottom) - rootY - top - height - 16)) });
      });
    });
  }, [navClearance]);
  React.useEffect(() => {
    const show = Keyboard.addListener("keyboardDidShow", (event) => { keyboardTop.current = event.endCoordinates.screenY; measureMenu(); });
    const hide = Keyboard.addListener("keyboardDidHide", () => { keyboardTop.current = Infinity; setSuggestionsOpen(false); measureMenu(); });
    if (Platform.OS === "web") window.visualViewport?.addEventListener("resize", measureMenu);
    return () => {
      show.remove(); hide.remove(); clearTimeout(blurTimer.current);
      if (Platform.OS === "web") window.visualViewport?.removeEventListener("resize", measureMenu);
    };
  }, [measureMenu]);
  React.useEffect(() => { if (menuVisible) requestAnimationFrame(measureMenu); }, [menuVisible, dimensions.width, dimensions.height, measureMenu]);
  const favorites = useLibrary((s) => s.favorites);
  // a new query starts on "All"
  React.useEffect(() => setSection(null), [query]);
  React.useEffect(() => {
    if (isFa) {
      sectionScroll.current?.scrollToEnd({ animated: false });
    }
  }, [query, isFa]);

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
  const suggestions = useMemo(() => q.trim() === query ? (first?.suggestions ?? []).filter((suggestion) =>
    suggestionFilter === "all" || (suggestion.kind ?? suggestionKind(suggestion.query)) === suggestionFilter) : [], [first, q, query, suggestionFilter]);
  React.useEffect(() => setActiveSuggestion(-1), [query, suggestionFilter]);
  const changeQuery = (value: string) => {
    clearTimeout(blurTimer.current);
    setQ(value); setSection(null); setSuggestionFilter("all"); setActiveSuggestion(-1); setSuggestionsOpen(true);
  };
  const selectSuggestion = (suggestion?: UptodateSearchSuggestion) => {
    if (suggestion) changeQuery(suggestion.query);
    dismissSuggestions();
  };
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
    <View ref={rootRef} onLayout={measureMenu} style={{ flex: 1, backgroundColor: colors.softBg }}>
      <View
        style={{
          backgroundColor: colors.cardBg,
          paddingHorizontal: 20,
          paddingTop: 18 + bleedTop,
          paddingBottom: 14,
          borderBottomWidth: 1,
          borderBottomColor: colors.trackBg,
          gap: 14,
          zIndex: 20,
        }}
      >
        <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
          <ChromeButton onPress={menuVisible ? dismissSuggestions : goBack} size={34}>
            <AppText weight="800" size={16} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <AppText accessibilityRole="header" weight="900" size={18} style={{ flex: 1 }}>
            {t("uptodateScreenTitle")}
          </AppText>
          <TourButton tour="uptodate" size={34} />
          <OfflineDownloadButton dataset="uptodate" tourId="utd.offline" />
          <LangToggleButton />
        </View>

        <TourTarget id="utd.search">
        <View
          ref={fieldRef} onLayout={measureMenu}
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 10,
            backgroundColor: colors.inputBg,
            borderWidth: 2,
            borderColor: colors.accent,
            borderRadius: 14,
            paddingHorizontal: 8,
            minHeight: 54,
          }}
        >
          <Pressable accessibilityRole="button" accessibilityLabel={isFa ? "جست‌وجوی عبارت" : "Search query"}
            onPress={() => selectSuggestion()} style={{ width: 32, minHeight: 44, alignItems: "center", justifyContent: "center" }}>
            <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth={1.8} aria-hidden>
              <Circle cx={10.5} cy={10.5} r={6.5} /><Path d="m16 16 5 5" />
            </Svg>
          </Pressable>
          <TextInput
            ref={inputRef} nativeID="uptodate-query"
            accessibilityLabel={t("uptodateSearchPlaceholder")}
            role="combobox" aria-autocomplete="list" aria-expanded={menuVisible}
            aria-controls="uptodate-suggestions"
            aria-activedescendant={menuVisible && activeSuggestion >= 0 ? `utd-suggestion-${activeSuggestion}` : undefined}
            value={q}
            onChangeText={changeQuery}
            onFocus={() => { clearTimeout(blurTimer.current); setSuggestionsOpen(true); measureMenu(); }}
            onBlur={() => {
              clearTimeout(blurTimer.current);
              blurTimer.current = setTimeout(() => {
                if (Platform.OS === "web" && document.getElementById("uptodate-suggestions")?.contains(document.activeElement)) return;
                setSuggestionsOpen(false);
              }, 160);
            }}
            onKeyPress={(event) => {
              const key = event.nativeEvent.key;
              if (key === "Escape") { event.preventDefault(); dismissSuggestions(); }
              else if (key === "ArrowDown" || key === "ArrowUp") {
                event.preventDefault(); setSuggestionsOpen(true);
                if (suggestions.length) setActiveSuggestion((i) => key === "ArrowDown" ? (i + 1) % suggestions.length : (i < 1 ? suggestions.length - 1 : i - 1));
              }
            }}
            onSubmitEditing={() => selectSuggestion(menuVisible && activeSuggestion >= 0 ? suggestions[activeSuggestion] : undefined)}
            returnKeyType="search"
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
          {q ? (
            <Pressable onPress={() => { changeQuery(""); inputRef.current?.focus(); }}
              accessibilityRole="button" accessibilityLabel={isFa ? "پاک کردن عبارت" : "Clear query"}
              style={{ width: 36, minHeight: 44, alignItems: "center", justifyContent: "center" }}>
              <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={colors.muted} strokeWidth={1.8} aria-hidden>
                <Path d="m6 6 12 12M18 6 6 18" />
              </Svg>
            </Pressable>
          ) : null}
        </View>
        </TourTarget>

        {sections.length > 0 ? (
          <ScrollView ref={sectionScroll} horizontal showsHorizontalScrollIndicator keyboardShouldPersistTaps="handled"
            onContentSizeChange={() => { if (isFa) sectionScroll.current?.scrollToEnd({ animated: false }); }}
            contentContainerStyle={{ flexDirection: row, gap: 8 }} style={{ flexGrow: 0 }}>
            <Chip label={`${t("articleSearchAll")} · ${n(first?.all ?? total)}`} on={!activeSection} onPress={() => setSection(null)} />
            {sections.map(([name, count]) => (
              <Chip key={name} label={name} count={n(count)} on={activeSection === name} onPress={() => setSection(name)} />
            ))}
          </ScrollView>
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
          <Favorites items={favorites} onOpen={(f) => navigate("uptodateOutline", { id: f.id, title: stripHtml(f.title) })} />
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
                onPress={() => navigate("uptodateOutline", { id: r.id, title: stripHtml(r.title) })}
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
      {menuVisible ? (
        <>
          <Pressable accessible={false} focusable={false} onPress={dismissSuggestions}
            style={{ position: "absolute", inset: 0, zIndex: 10 }} />
          <View style={{ position: "absolute", top: menuPosition.top, left: menuPosition.left, width: menuPosition.width, zIndex: 30 }}>
            <UptodateSuggestionMenu query={q} suggestions={suggestions} filter={suggestionFilter}
              onFilter={(filter) => { setSuggestionFilter(filter); setActiveSuggestion(-1); }}
              active={activeSuggestion} onActive={setActiveSuggestion} onSelect={selectSuggestion}
              loading={q.trim() !== query || (isFetching && !first)} failed={!!error}
              maxHeight={menuPosition.maxHeight} />
          </View>
        </>
      ) : null}
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
      accessibilityRole="button"
      accessibilityState={{ selected: on }}
      aria-pressed={on}
      accessibilityLabel={count ? `${label}, ${count}` : label}
      style={{
        maxWidth: 280,
        minHeight: 44,
        alignItems: "center",
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
    const text = stripHtml(result.title);
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
        <AppText weight="700" size={11.5} color={colors.accent} style={[LTR, { lineHeight: 16 }]}>
          {result.section}
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
          {"★" /* taste-skill-ignore: existing monochrome favorite-state icon. */}
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
                <AppText weight="700" size={11.5} color={colors.accent} style={[LTR, { lineHeight: 16 }]}>
                  {f.section}
                </AppText>
              ) : null}
              <AppText weight="800" size={14.5} style={[LTR, { lineHeight: 20 }]}>
                {stripHtml(f.title)}
              </AppText>
            </View>
            <Pressable
              onPress={() => toggleFavorite(f)}
              hitSlop={8}
              accessibilityLabel={t("favoriteRemove")}
              style={{ width: 40, height: 40, alignItems: "center", justifyContent: "center" }}
            >
              <AppText weight="800" size={18} color="#E0A526">
                {"★" /* taste-skill-ignore: existing monochrome favorite-state icon. */}
              </AppText>
            </Pressable>
          </Pressable>
        ))
      )}
    </View>
  );
}
