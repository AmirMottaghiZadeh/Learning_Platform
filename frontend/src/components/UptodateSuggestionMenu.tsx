import React, { useEffect, useRef } from "react";
import { Platform, Pressable, ScrollView, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import type { UptodateSearchSuggestion, UptodateSuggestionKind } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { normalizeSearch, suggestionKind } from "@/offline/uptodateSearchCatalog";
import { useTheme } from "@/theme/ThemeProvider";
import { stripHtml } from "@/utils/html";

export type SuggestionFilter = "all" | UptodateSuggestionKind;
const LTR = { writingDirection: "ltr" as const, textAlign: "left" as const };

export function UptodateSuggestionMenu({ suggestions, query, filter, onFilter, active, onActive, onSelect, loading, failed, maxHeight }: {
  suggestions: UptodateSearchSuggestion[];
  query: string;
  filter: SuggestionFilter;
  onFilter: (filter: SuggestionFilter) => void;
  active: number;
  onActive: (index: number) => void;
  onSelect: (suggestion: UptodateSearchSuggestion) => void;
  loading: boolean;
  failed: boolean;
  maxHeight: number;
}) {
  const { colors } = useTheme();
  const { isFa, n, row } = useLang();
  const list = useRef<ScrollView>(null);
  const filters = useRef<ScrollView>(null);
  const positions = useRef<Record<number, { y: number; height: number }>>({});
  const viewport = useRef({ y: 0, height: 0 });
  const names = isFa
    ? { all: "همه", treatment: "درمان", diagnosis: "تشخیص", followup: "پیگیری", general: "موضوع مرجع" }
    : { all: "All", treatment: "Treatment", diagnosis: "Diagnosis", followup: "Follow-up", general: "Reference topic" };
  useEffect(() => {
    const rect = positions.current[active], view = viewport.current;
    if (!rect || active < 0) return;
    if (rect.y < view.y) list.current?.scrollTo({ y: rect.y, animated: false });
    else if (rect.y + rect.height > view.y + view.height) {
      list.current?.scrollTo({ y: rect.y + rect.height - view.height, animated: false });
    }
  }, [active]);
  // Prevent real and touch-emulated mouse focus changes, keeping the mobile
  // keyboard open on category taps. Touchstart stays available for presses
  // and scrolling; canceling it suppresses React Native Web's click event.
  const focusProps = Platform.OS === "web" ? {
    onMouseDown: (event: { preventDefault: () => void }) => event.preventDefault(),
  } as object : {};
  return (
    <View nativeID="uptodate-suggestions" testID="uptodate-suggestion-menu"
      style={{ maxHeight, borderWidth: 1, borderColor: colors.boxedBorder, borderRadius: 12, backgroundColor: colors.cardBg, overflow: "hidden" }}>
      <View style={{ flexDirection: row, justifyContent: "space-between", gap: 8, paddingHorizontal: 14, paddingTop: 10, paddingBottom: 4 }}>
        <AppText muted size={13}>{isFa ? "پیشنهادها به ترتیب اولویت" : "Suggested searches"}</AppText>
        <AppText muted size={12} accessibilityLiveRegion="polite">
          {loading ? (isFa ? "در حال دریافت…" : "Loading…") : `${n(suggestions.length)} ${isFa ? "عبارت" : "queries"}`}
        </AppText>
      </View>
      <ScrollView ref={filters} horizontal showsHorizontalScrollIndicator={false} keyboardShouldPersistTaps="always"
        onContentSizeChange={() => { if (isFa) filters.current?.scrollToEnd({ animated: false }); }}
        style={{ flexGrow: 0, flexShrink: 0 }} contentContainerStyle={{ flexDirection: row, paddingHorizontal: 8 }}>
        {(["all", "treatment", "diagnosis", "followup"] as const).map((key) => (
          <Pressable key={key} accessibilityRole="button" accessibilityState={{ selected: filter === key }}
            aria-pressed={filter === key} {...focusProps} onPress={() => onFilter(key)}
            style={{ minHeight: 44, justifyContent: "center", paddingHorizontal: 12, borderBottomWidth: 2, borderBottomColor: filter === key ? colors.ink : "transparent" }}>
            <AppText size={13} weight={filter === key ? "700" : "400"}>{names[key]}</AppText>
          </Pressable>
        ))}
      </ScrollView>
      <ScrollView ref={list}
        // Native exposes a list; the web combobox needs the more specific ARIA role.
        {...(Platform.OS === "web" ? { role: "listbox" } as object : { accessibilityRole: "list" as const })}
        aria-label={isFa ? "عبارت‌های پیشنهادی" : "Suggested queries"}
        keyboardShouldPersistTaps="always" nestedScrollEnabled style={{ flexGrow: 0, flexShrink: 1 }}
        onLayout={(event) => { viewport.current.height = event.nativeEvent.layout.height; }}
        onScroll={(event) => { viewport.current.y = event.nativeEvent.contentOffset.y; }} scrollEventThrottle={16}>
        {suggestions.map((suggestion, i) => {
          const label = stripHtml(suggestion.label), prefix = normalizeSearch(query);
          const matched = normalizeSearch(label).startsWith(prefix) ? prefix.length : 0;
          const kind = suggestion.kind ?? suggestionKind(suggestion.query);
          const count = typeof suggestion.count === "number" ? `${n(suggestion.count)} ${isFa ? "مقالهٔ مرتبط" : "related articles"}` : "";
          const meta = [names[kind], count].filter(Boolean).join(" · ");
          return (
            <Pressable key={suggestion.query} nativeID={`utd-suggestion-${i}`} role="option"
              accessibilityState={{ selected: active === i }} aria-selected={active === i}
              accessibilityLabel={`${label}, ${meta}`} focusable={false}
              onLayout={(event) => { positions.current[i] = event.nativeEvent.layout; }}
              {...focusProps} onPress={() => onSelect(suggestion)} onHoverIn={() => onActive(i)}
              style={{ flexDirection: "row", alignItems: "center", gap: 10, minHeight: 68, paddingVertical: 10, paddingHorizontal: 14,
                borderTopWidth: i ? 1 : 0, borderTopColor: colors.trackBg, backgroundColor: active === i ? colors.softBg : colors.cardBg }}>
              <AppText muted size={12} style={[LTR, { width: 16 }]}>{n(i + 1)}</AppText>
              <View style={{ flex: 1, minWidth: 0 }}>
                <AppText size={15} style={LTR}>
                  <AppText size={15} weight="600" color={colors.accent} style={LTR}>{label.slice(0, matched)}</AppText>
                  {label.slice(matched)}
                </AppText>
                <AppText muted size={13} style={{ textAlign: "left", marginTop: 2 }}>{meta}</AppText>
              </View>
              <Svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke={colors.muted} strokeWidth={1.6} aria-hidden>
                <Path d="M19 4v10H5m5-5-5 5 5 5" />
              </Svg>
            </Pressable>
          );
        })}
        {!suggestions.length ? (
          <AppText muted size={13} style={{ padding: 16 }} accessibilityLiveRegion="polite">
            {query.trim().length < 2 ? (isFa ? "حداقل دو حرف بنویسید." : "Type at least two characters.")
              : loading ? (isFa ? "در حال پیدا کردن پیشنهادها…" : "Finding suggestions…")
                : failed ? (isFa ? "پیشنهادها دریافت نشدند؛ دوباره تلاش کنید." : "Suggestions could not load. Please try again.")
                  : filter !== "all" ? (isFa ? "در این گروه پیشنهادی نیست؛ «همه» را ببینید." : "No suggestions in this category. Try All.")
                    : (isFa ? "پیشنهادی نیست؛ می‌توانید خود عبارت را جست‌وجو کنید." : "No suggestions. You can search your own query.")}
          </AppText>
        ) : null}
      </ScrollView>
      <AppText muted size={12} style={{ flexShrink: 0, borderTopWidth: 1, borderTopColor: colors.trackBg, paddingHorizontal: 14, paddingVertical: 7 }}>
        {Platform.OS === "web" ? (isFa ? "↑ ↓ انتخاب · Enter جست‌وجو · Esc بستن" : "↑ ↓ select · Enter search · Esc close")
          : (isFa ? "برای جست‌وجو، عبارت مورد نظر را لمس کنید." : "Tap a suggestion to search.")}
      </AppText>
    </View>
  );
}
