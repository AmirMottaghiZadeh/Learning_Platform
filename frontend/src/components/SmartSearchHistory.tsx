import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { Modal, Pressable, SectionList, StyleSheet, useWindowDimensions, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import Svg, { Path } from "react-native-svg";

import { aiLabApi, LabHistoryEntry } from "@/api/aiLab";
import { AppText } from "@/components/primitives/AppText";
import { Chevron } from "@/components/primitives/Chevron";
import { ChromeButton } from "@/components/ScreenChrome";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, radius, spacing } from "@/theme/tokens";
import { useReducedMotion } from "@/utils/useReducedMotion";

type HistoryDay = { key: string; title: string; data: LabHistoryEntry[] };

function groupByDay(entries: LabHistoryEntry[], isFa: boolean, formatDate: Intl.DateTimeFormat) {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const todayKey = today.toDateString();
  const yesterdayKey = yesterday.toDateString();
  const days = new Map<string, HistoryDay>();

  for (const entry of entries) {
    const date = new Date(entry.created_at);
    const key = date.toDateString();
    const existing = days.get(key);
    if (existing) {
      existing.data.push(entry);
      continue;
    }
    const title = key === todayKey ? (isFa ? "امروز" : "Today")
      : key === yesterdayKey ? (isFa ? "دیروز" : "Yesterday") : formatDate.format(date);
    days.set(key, { key, title, data: [entry] });
  }
  return [...days.values()];
}

export function SmartSearchHistory({ userId, visible, opening, openError, onClose, onOpen }: {
  userId: number | null; visible: boolean; opening: string | null; openError: boolean;
  onClose: () => void; onOpen: (entry: LabHistoryEntry) => void;
}) {
  const { colors, isDark } = useTheme();
  const { isFa, row, n } = useLang();
  const { height } = useWindowDimensions();
  const reducedMotion = useReducedMotion();
  const history = useInfiniteQuery({
    queryKey: ["smart-search-history", userId],
    queryFn: ({ pageParam }) => aiLabApi.history(pageParam ?? undefined),
    initialPageParam: null as string | null,
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    enabled: visible && userId !== null,
    gcTime: 0,
  });
  const entries = history.data?.pages.flatMap((page) => page.results) ?? [];
  const locale = isFa ? "fa-IR" : "en";
  const days = groupByDay(entries, isFa, new Intl.DateTimeFormat(locale, { dateStyle: "medium" }));
  const time = new Intl.DateTimeFormat(locale, { hour: "numeric", minute: "2-digit" });
  const canLoadMore = history.hasNextPage || history.isFetchNextPageError;
  const moreLabel = history.isFetchingNextPage ? (isFa ? "در حال دریافت…" : "Loading…")
    : history.isFetchNextPageError ? (isFa ? "بارگذاری نشد. دوباره تلاش کنید" : "Could not load more. Try again")
      : isFa ? "جست‌وجوهای بیشتر" : "More searches";

  return <Modal visible={visible} transparent animationType={reducedMotion ? "none" : "slide"} onRequestClose={onClose}>
    <View style={{ flex: 1, justifyContent: "flex-end", alignItems: "center" }}>
      <Pressable testID="smart-search-history-backdrop" accessible={false} focusable={false} onPress={onClose}
        style={[StyleSheet.absoluteFill, { backgroundColor: isDark ? "rgba(8,14,11,0.55)" : "rgba(22,39,32,0.25)" }]} />
      <SafeAreaView edges={["bottom", "left", "right"]} testID="smart-search-history-panel" accessibilityViewIsModal
        onAccessibilityEscape={onClose}
        style={{ direction: "ltr", width: "100%", maxWidth: layout.appMaxWidth + 100, height: Math.min(560, height * 0.76),
          backgroundColor: colors.cardBg, boxShadow: colors.cardShadow, overflow: "hidden",
          borderTopLeftRadius: radius.shell, borderTopRightRadius: radius.shell }}>
        <View style={{ height: 4, width: 36, alignSelf: "center", borderRadius: radius.chip,
          marginTop: spacing.sm, marginBottom: spacing.md, backgroundColor: colors.trackBg }} />
        <View style={{ flexDirection: row, alignItems: "center", paddingHorizontal: spacing.lg, gap: spacing.md }}>
          <View style={{ flex: 1, minWidth: 0 }}>
            <AppText accessibilityRole="header" aria-level={2} size={18} weight="800">
              {isFa ? "جست‌وجوهای من" : "My searches"}
            </AppText>
            <AppText size={12} muted>{isFa ? "برای دیدن پاسخ قبلی، پرسش را انتخاب کنید." : "Choose a question to see its saved answer."}</AppText>
          </View>
          <ChromeButton onPress={onClose} accessibilityLabel={isFa ? "بستن تاریخچه" : "Close history"}>
            <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={colors.ink} strokeWidth={1.8} aria-hidden>
              <Path d="m6 6 12 12M6 18 18 6" strokeLinecap="round" />
            </Svg>
          </ChromeButton>
        </View>
        <SectionList sections={days} keyExtractor={(entry) => entry.job_id} stickySectionHeadersEnabled={false}
          style={{ flex: 1 }} contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: spacing.lg }}
          ListHeaderComponent={openError ? <AppText accessibilityRole="alert" size={13} color={colors.denyLabel} style={{ marginTop: spacing.md }}>
            {isFa ? "نتیجه باز نشد. دوباره انتخابش کنید." : "Could not open the search. Select it again to retry."}
          </AppText> : null}
          ListEmptyComponent={<View style={{ paddingVertical: spacing.xl }}>
            {history.isPending ? <AppText accessibilityLiveRegion="polite" size={13} muted>{isFa ? "در حال دریافت تاریخچه…" : "Loading search history…"}</AppText>
              : history.isError ? <Pressable accessibilityRole="button" onPress={() => void history.refetch()} style={{ minHeight: 44, justifyContent: "center" }}>
                <AppText size={13} color={colors.denyLabel}>{isFa ? "تاریخچه بارگذاری نشد. دوباره تلاش کنید" : "Could not load history. Try again"}</AppText>
              </Pressable>
                : <AppText size={13} muted>{isFa ? "جست‌وجوهای قبلی‌تان اینجا نمایش داده می‌شوند." : "Your past searches will appear here."}</AppText>}
          </View>}
          renderSectionHeader={({ section }) => <AppText accessibilityRole="header" aria-level={3} size={12} muted
            style={{ paddingTop: spacing.md, paddingBottom: spacing.xs }}>
            {section.title}
          </AppText>}
          ItemSeparatorComponent={() => <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: colors.sheetLine }} />}
          renderItem={({ item }) => {
            const busy = opening === item.job_id;
            const disabled = opening !== null || item.status === "unavailable";
            const statusLabel = busy ? (isFa ? "در حال بازکردن…" : "Opening…")
              : item.status === "failed" ? (isFa ? "جست‌وجوی ناموفق" : "Failed search") : null;
            return <Pressable testID="smart-search-history-entry" accessibilityRole="button" accessibilityState={{ busy, disabled }}
              disabled={disabled} onPress={() => onOpen(item)}
              style={({ pressed }) => ({ flexDirection: row, alignItems: "center", gap: spacing.md, minHeight: 54,
                paddingVertical: spacing.sm, paddingHorizontal: spacing.xs, borderRadius: radius.input,
                backgroundColor: pressed || busy ? colors.leitnerActiveBg : "transparent" })}>
              <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                <AppText size={14} weight="700" numberOfLines={2} muted={item.status === "unavailable"}>
                  {item.question || (isFa ? "جست‌وجو در دسترس نیست" : "Search unavailable")}
                </AppText>
                {statusLabel ? <AppText size={11} muted>{statusLabel}</AppText> : null}
              </View>
              <View style={{ flexDirection: row, alignItems: "center", gap: spacing.xs }}>
                <AppText size={11} muted style={{ writingDirection: "ltr" }}>{time.format(new Date(item.created_at))}</AppText>
                {item.status !== "unavailable" ? <Chevron color={colors.accent} /> : null}
              </View>
            </Pressable>;
          }}
          ListFooterComponent={canLoadMore ? <Pressable accessibilityRole="button" disabled={history.isFetchingNextPage}
            onPress={() => void history.fetchNextPage()} style={{ minHeight: 44, justifyContent: "center", marginTop: spacing.sm }}>
            <AppText size={12} color={history.isFetchNextPageError ? colors.denyLabel : colors.accent}>{moreLabel}</AppText>
          </Pressable> : entries.length > 0 ? <AppText size={12} color={colors.accent} style={{ marginTop: spacing.md }}>
            {isFa ? `${n(entries.length)} جست‌وجوی ذخیره‌شده` : `${entries.length} saved ${entries.length === 1 ? "search" : "searches"}`}
          </AppText> : null}
        />
      </SafeAreaView>
    </View>
  </Modal>;
}
