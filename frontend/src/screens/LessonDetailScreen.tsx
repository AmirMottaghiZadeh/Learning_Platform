import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { NativeScrollEvent, NativeSyntheticEvent, Pressable, ScrollView, TextInput, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { LessonSection, SectionTone } from "@/api/types";
import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

function toneColors(tone: SectionTone, c: ReturnType<typeof useTheme>["colors"]) {
  switch (tone) {
    case "deny":
      return { bg: c.denyBg, border: c.denyBorder, label: c.denyLabel };
    case "boxed":
      return { bg: c.denyBg, border: c.boxedBorder, label: c.boxedInk };
    case "caution":
      return { bg: c.cautBg, border: c.cautBorder, label: c.cautLabel };
    case "special":
      return { bg: c.specBg, border: c.specBorder, label: c.specLabel };
    default:
      return { bg: "transparent", border: "transparent", label: c.accent };
  }
}

export function LessonDetailScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const code = String(useNav((s) => s.params.code ?? ""));
  const slug = String(useNav((s) => s.params.slug ?? ""));
  const queryClient = useQueryClient();

  const [progressPct, setProgressPct] = useState(4);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [openEn, setOpenEn] = useState<Record<string, boolean>>({});
  const marked = useRef(false);

  const { data, isLoading } = useQuery({
    queryKey: ["chapter", code],
    queryFn: () => lessonsApi.chapter(code),
    enabled: !!code,
  });

  const drug = data?.drugs.find((d) => d.slug === slug) ?? data?.drugs[0];

  const markRead = useMutation({
    mutationFn: () => lessonsApi.saveProgress(code, { drug_slug: slug, scroll_pct: 100 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", code] });
      queryClient.invalidateQueries({ queryKey: ["lesson-groups"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const blocks: LessonSection[] = useMemo(() => {
    const list = drug?.lesson_sections ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (b) =>
        (isFa ? b.title_fa : b.title_en).toLowerCase().includes(q) ||
        (isFa ? b.text_fa : b.text_en).toLowerCase().includes(q),
    );
  }, [drug, query, isFa]);

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
    const max = contentSize.height - layoutMeasurement.height;
    const pct = max > 0 ? Math.min(100, Math.round((contentOffset.y / max) * 100)) : 100;
    setProgressPct(Math.max(4, pct));
    if (pct > 92 && !marked.current && slug) {
      marked.current = true;
      markRead.mutate();
    }
  };

  if (isLoading) return <LoadingState />;

  const hasBoxed = (drug?.sections ?? []).some((s) => s.field === "boxed_warning" && s.has_summary);
  const hasAbuse = (drug?.sections ?? []).some((s) => s.field === "abuse" && s.has_summary);
  const mins = Math.max(
    3,
    Math.round((drug?.lesson_sections.reduce((a, b) => a + (isFa ? b.text_fa : b.text_en).length, 0) ?? 0) / 620),
  );

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 18 }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
            <ChromeButton onPress={goBack} size={30}>
              <AppText weight="800" size={15} color={colors.ink}>
                {isFa ? "›" : "‹"}
              </AppText>
            </ChromeButton>
            <AppText weight="800" size={12} muted>
              {data ? (isFa ? data.name_fa : data.name_en) : code}
            </AppText>
          </View>
          <ChromeButton onPress={() => setSearchOpen((v) => !v)} size={30}>
            <AppText size={14} color={colors.muted}>
              ⌕
            </AppText>
          </ChromeButton>
        </View>

        <View style={{ height: 3, backgroundColor: colors.trackBg, borderRadius: 2, marginTop: 13 }}>
          <View style={{ width: `${progressPct}%`, height: 3, backgroundColor: colors.accent, borderRadius: 2 }} />
        </View>

        {searchOpen ? (
          <View
            style={{
              flexDirection: row,
              alignItems: "center",
              gap: 9,
              backgroundColor: colors.softBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              borderRadius: 13,
              paddingHorizontal: 12,
              paddingVertical: 8,
              marginTop: 12,
            }}
          >
            <AppText muted>⌕</AppText>
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder={isFa ? "جست‌وجو در فصل…" : "Search this chapter…"}
              placeholderTextColor={colors.muted}
              autoFocus
              style={{
                flex: 1,
                fontFamily: fontFamily("600"),
                fontSize: 13,
                color: colors.ink,
                textAlign: isFa ? "right" : "left",
                padding: 0,
              }}
            />
          </View>
        ) : null}
      </View>

      <ScrollView
        style={{ flex: 1 }}
        onScroll={onScroll}
        scrollEventThrottle={64}
        contentContainerStyle={{ paddingHorizontal: 22, paddingTop: 20, paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      >
        <AppText weight="900" size={26} style={{ lineHeight: 38 }}>
          {drug?.name}
        </AppText>
        <AppText weight="700" size={13} muted style={{ marginTop: 4 }}>
          {[...(drug?.pharm_classes ?? []), ...(drug?.atc_codes ?? []).map((a) => a.code)].join(" · ")}
        </AppText>

        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6, marginTop: 13 }}>
          {hasBoxed ? (
            <Badge bg={colors.boxedBorder} fg={colors.cardBg} text={isFa ? "جعبه‌سیاه" : "Boxed"} />
          ) : null}
          {hasAbuse ? (
            <Badge bg={colors.specBg} fg={colors.specLabel} text={isFa ? "کنترل‌شده" : "Controlled"} border={colors.specBorder} />
          ) : null}
          <Badge
            bg={colors.softBg}
            fg={colors.muted}
            border={colors.trackBg}
            text={isFa ? `${n(mins)} دقیقه` : `${mins} min`}
          />
        </View>

        {blocks.length === 0 ? (
          <AppText muted weight="600" size={13} style={{ marginTop: 24 }}>
            {isFa ? "چیزی پیدا نشد." : "Nothing found."}
          </AppText>
        ) : (
          blocks.map((b) => {
            const tc = toneColors(b.tone, colors);
            const isBox = b.tone !== "info";
            const enOpen = !!openEn[b.key];
            return (
              <View
                key={b.key}
                style={[
                  { marginTop: 20 },
                  isBox && {
                    backgroundColor: tc.bg,
                    borderWidth: 1,
                    borderColor: tc.border,
                    borderRadius: 14,
                    padding: 14,
                  },
                ]}
              >
                <AppText weight="900" size={isBox ? 14 : 18} color={isBox ? tc.label : colors.ink}>
                  {isFa ? b.title_fa : b.title_en}
                </AppText>
                <AppText
                  size={15}
                  weight="500"
                  color={colors.proseInk}
                  style={{ lineHeight: 30, marginTop: 8 }}
                >
                  {isFa ? b.text_fa : b.text_en}
                </AppText>
                {(isFa ? b.text_en : b.text_fa).trim() ? (
                  <>
                    <Pressable
                      onPress={() => setOpenEn((s) => ({ ...s, [b.key]: !s[b.key] }))}
                      style={{ marginTop: 10, flexDirection: row, alignItems: "center", gap: 6 }}
                    >
                      <AppText weight="800" size={12.5} color={colors.accent}>
                        {isFa ? "نسخهٔ انگلیسی" : "نسخهٔ فارسی"} {enOpen ? "▲" : "▼"}
                      </AppText>
                    </Pressable>
                    {enOpen ? (
                      <View
                        style={{
                          backgroundColor: colors.softBg,
                          borderRadius: 12,
                          padding: 12,
                          marginTop: 9,
                        }}
                      >
                        <AppText
                          size={12.5}
                          weight="600"
                          color={colors.muted}
                          style={{ lineHeight: 24, textAlign: isFa ? "left" : "right", writingDirection: isFa ? "ltr" : "rtl" }}
                        >
                          {isFa ? b.text_en : b.text_fa}
                        </AppText>
                      </View>
                    ) : null}
                  </>
                ) : null}
              </View>
            );
          })
        )}

        <Pressable
          onPress={() => navigate("quiz")}
          style={{
            marginTop: 28,
            backgroundColor: colors.accent + "12",
            borderWidth: 1,
            borderColor: colors.trackBg,
            borderRadius: 16,
            padding: 16,
          }}
        >
          <AppText weight="800" size={14}>
            {isFa ? "نکته‌های آزمونی این فصل" : "Exam points from this chapter"}
          </AppText>
          <AppText muted weight="600" size={12} style={{ marginTop: 4 }}>
            {isFa ? "از هشدارها و منع‌های همین فصل ساخته شده" : "Built from this chapter's warnings and limits"}
          </AppText>
          <AppText weight="900" size={13} color={colors.accent} style={{ marginTop: 10 }}>
            {isFa ? "شروع خودآزمایی ‹" : "Start self-test ›"}
          </AppText>
        </Pressable>
      </ScrollView>
    </View>
  );
}

function Badge({ bg, fg, text, border }: { bg: string; fg: string; text: string; border?: string }) {
  return (
    <View
      style={{
        backgroundColor: bg,
        borderWidth: border ? 1 : 0,
        borderColor: border,
        borderRadius: 8,
        paddingHorizontal: 10,
        paddingVertical: 5,
      }}
    >
      <AppText weight="900" size={11} color={fg}>
        {text}
      </AppText>
    </View>
  );
}
