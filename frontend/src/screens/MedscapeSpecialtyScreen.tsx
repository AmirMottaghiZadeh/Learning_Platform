import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { Pressable, ScrollView, TextInput, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeArticleListItem, MedscapeKind } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout, spacing } from "@/theme/tokens";

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const ROW_HEIGHT = 46;
const SECTION_HEADER_HEIGHT = 30;

type Section = { title: string; data: MedscapeArticleListItem[] };

function groupAlphabetically(items: MedscapeArticleListItem[]): Section[] {
  const byLetter = new Map<string, MedscapeArticleListItem[]>();
  for (const item of [...items].sort((a, b) => a.title.localeCompare(b.title))) {
    const first = item.title.trim().charAt(0).toUpperCase();
    const letter = /[A-Z]/.test(first) ? first : "#";
    if (!byLetter.has(letter)) byLetter.set(letter, []);
    byLetter.get(letter)!.push(item);
  }
  const letters = [...byLetter.keys()].sort((a, b) => {
    if (a === "#") return 1;
    if (b === "#") return -1;
    return a.localeCompare(b);
  });
  return letters.map((letter) => ({ title: letter, data: byLetter.get(letter)! }));
}

/** Each section's scroll offset, computed directly from fixed row/header
 * heights -- not from RN's onLayout (which never fired reliably for these
 * rows in the web preview) or from SectionList's own index/offset
 * machinery (which drifted to the wrong section in testing). A direct,
 * self-computed offset passed straight to ScrollView.scrollTo sidesteps
 * both: it only requires the rows to have the fixed height we already
 * render them at (hence the single-line title below). */
function buildOffsets(sections: Section[]): Map<string, number> {
  const offsets = new Map<string, number>();
  let y = 0;
  for (const section of sections) {
    offsets.set(section.title, y);
    y += SECTION_HEADER_HEIGHT + section.data.length * ROW_HEIGHT;
  }
  return offsets;
}

/** A–Z sectioned list for one (kind, category, specialty), with a jump rail
 * -- the drill-down target from the specialty grid in MedscapeBrowseScreen,
 * replacing what used to be an inline accordion of a potentially huge flat
 * list. */
export function MedscapeSpecialtyScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const kind = String(useNav((s) => s.params.kind ?? "disease")) as MedscapeKind;
  const category = String(useNav((s) => s.params.category ?? ""));
  const specialty = String(useNav((s) => s.params.specialty ?? ""));

  const [q, setQ] = useState("");
  const scrollRef = useRef<ScrollView>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["medscape-articles", kind, category, specialty],
    queryFn: () => medscapeApi.bySpecialty(kind, category, specialty),
  });

  const items = data ?? [];
  const query = q.trim().toLowerCase();
  const filtered = query.length > 0 ? items.filter((a) => a.title.toLowerCase().includes(query)) : items;
  const sections = useMemo(() => groupAlphabetically(filtered), [filtered]);
  const availableLetters = useMemo(() => new Set(sections.map((s) => s.title)), [sections]);
  const offsets = useMemo(() => buildOffsets(sections), [sections]);

  const openArticle = (slug: string) => navigate("medscapeArticle", { slug });

  const jumpTo = (letter: string) => {
    const y = offsets.get(letter);
    if (y === undefined) return;
    scrollRef.current?.scrollTo({ y, animated: true });
  };

  if (isLoading) return <LoadingState />;

  return (
    <Screen scroll={false} padded={false}>
      <View style={{ flex: 1, padding: layout.screenPadding, paddingBottom: 0 }}>
        <ScreenChrome title={specialty} onBack={goBack} />

        <AppText muted weight="700" size={12} style={{ marginBottom: 10, textAlign: "left", writingDirection: "ltr" }}>
          {items.length} {t("medscapeArticleCount")}
        </AppText>

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

        <View style={{ flex: 1, flexDirection: "row" }}>
          {sections.length === 0 ? (
            <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
              {t("medscapeNoLocalResults")}
            </AppText>
          ) : (
            <ScrollView
              ref={scrollRef}
              style={{ flex: 1 }}
              contentContainerStyle={{ paddingBottom: layout.bottomNavHeight + 24, paddingRight: 10 }}
              showsVerticalScrollIndicator={false}
            >
              {sections.map((section) => (
                <View key={section.title}>
                  <View style={{ height: SECTION_HEADER_HEIGHT, justifyContent: "center", backgroundColor: colors.appBg }}>
                    <AppText
                      weight="800"
                      size={12}
                      muted
                      style={{ letterSpacing: 0.4, textAlign: "left", writingDirection: "ltr" }}
                    >
                      {section.title}
                    </AppText>
                  </View>
                  {section.data.map((article) => (
                    <Pressable key={article.slug} onPress={() => openArticle(article.slug)}>
                      <View
                        style={{
                          height: ROW_HEIGHT,
                          justifyContent: "center",
                          borderBottomWidth: 1,
                          borderBottomColor: colors.trackBg,
                        }}
                      >
                        <AppText
                          weight="600"
                          size={13.5}
                          numberOfLines={1}
                          style={{ textAlign: "left", writingDirection: "ltr" }}
                        >
                          {article.title}
                        </AppText>
                      </View>
                    </Pressable>
                  ))}
                </View>
              ))}
            </ScrollView>
          )}

          <View style={{ width: 18, alignItems: "center", paddingTop: 6, gap: 1 }}>
            {ALPHABET.map((letter) => {
              const enabled = availableLetters.has(letter);
              return (
                <Pressable key={letter} onPress={() => enabled && jumpTo(letter)} hitSlop={2}>
                  <AppText
                    weight={enabled ? "800" : "600"}
                    size={9.5}
                    color={enabled ? colors.accent : colors.trackBg}
                  >
                    {letter}
                  </AppText>
                </Pressable>
              );
            })}
          </View>
        </View>
      </View>
    </Screen>
  );
}
