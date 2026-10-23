import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { ApiError } from "@/api/client";
import { UptodateSearchResult } from "@/api/types";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { OfflineDownloadButton } from "@/components/offline/OfflineDownloadButton";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { uptodateSource } from "@/offline/sources";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout } from "@/theme/tokens";
import { shortDate } from "@/utils/uptodateOutline";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };
// The busiest sections among the results get a filter chip; the rest are
// still under "All".
const MAX_SECTION_CHIPS = 4;

function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** UpToDate search (design option 1): a white header with the search field
 * and one chip per clinical section among the results, then a card per
 * topic with its section, title, a snippet around the hit and its date. */
export function UptodateScreen() {
  const { t, n, row, isFa } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const [section, setSection] = useState<string | null>(null);

  const { data, isFetching, error } = useQuery({
    queryKey: ["uptodate-search", query],
    queryFn: () => uptodateSource.search(query),
    enabled: query.length >= 2,
    retry: false,
  });

  const locked = error instanceof ApiError && error.status === 503;
  const rows = useMemo(() => data ?? [], [data]);
  const sections = useMemo(() => {
    const counts = new Map<string, number>();
    for (const r of rows) if (r.section) counts.set(r.section, (counts.get(r.section) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows]);
  const activeSection = section && sections.some(([s]) => s === section) ? section : null;
  const visible = activeSection ? rows.filter((r) => r.section === activeSection) : rows;
  const words = useMemo(() => (query.match(/[A-Za-z0-9؀-ۿ]+/g) ?? []).slice(0, 8), [query]);

  return (
    <View style={{ flex: 1, backgroundColor: colors.softBg }}>
      <View
        style={{
          backgroundColor: colors.cardBg,
          paddingHorizontal: 20,
          paddingTop: 18,
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
          <OfflineDownloadButton dataset="uptodate" />
          <LangToggleButton />
        </View>

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

        {sections.length > 1 ? (
          <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
            <Chip label={`${t("articleSearchAll")} · ${n(rows.length)}`} on={!activeSection} onPress={() => setSection(null)} />
            {sections.slice(0, MAX_SECTION_CHIPS).map(([name, count]) => (
              <Chip key={name} label={`${name} · ${n(count)}`} on={activeSection === name} onPress={() => setSection(name)} />
            ))}
          </View>
        ) : null}
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 10, paddingBottom: layout.bottomNavHeight + 24 }}>
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
        ) : (
          visible.map((r) => (
            <ResultCard
              key={r.id}
              result={r}
              words={words}
              onPress={() => navigate("uptodateOutline", { id: r.id, title: r.title })}
              shadow={shadows.raisedSm}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
}

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={{
        paddingHorizontal: 12,
        paddingVertical: 5,
        borderRadius: 999,
        backgroundColor: on ? colors.accent : colors.softBg,
        borderWidth: 1,
        borderColor: on ? colors.accent : colors.trackBg,
      }}
    >
      <AppText weight={on ? "800" : "700"} size={12} color={on ? colors.onAccent : colors.ink} style={{ lineHeight: 18 }}>
        {label}
      </AppText>
    </Pressable>
  );
}

function ResultCard({
  result,
  words,
  onPress,
  shadow,
}: {
  result: UptodateSearchResult;
  words: string[];
  onPress: () => void;
  shadow: object;
}) {
  const { colors } = useTheme();
  const snippet = useMemo(() => {
    if (!result.snippet || words.length === 0) return result.snippet;
    const re = new RegExp(`(${words.map(escapeRegExp).join("|")})`, "gi");
    return result.snippet.split(re).map((part, i) =>
      i % 2 === 1 ? (
        <Text key={i} style={{ backgroundColor: `${colors.accent}2E`, color: colors.ink, borderRadius: 3 }}>
          {part}
        </Text>
      ) : (
        part
      ),
    );
  }, [result.snippet, words, colors]);

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
        {result.title}
      </AppText>
      {result.snippet ? (
        <AppText weight="500" size={12.5} muted style={[LTR, { lineHeight: 19 }]}>
          {snippet}
        </AppText>
      ) : null}
      {result.updated ? (
        <AppText weight="600" size={11} muted style={[LTR, { lineHeight: 16, opacity: 0.85 }]}>
          Updated {shortDate(result.updated)}
        </AppText>
      ) : null}
    </Pressable>
  );
}
