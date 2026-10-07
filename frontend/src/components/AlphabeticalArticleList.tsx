import React, { useMemo, useRef } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { MedscapeArticleListItem } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";

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

/** An A-Z sectioned list with a jump rail, for one already-fetched set of
 * articles -- shared by MedscapeSpecialtyScreen (one disease specialty) and
 * MedscapeGuidelinesScreen (one guideline type), which differ above this
 * point (how they fetch/filter `items`) but render the result identically. */
export function AlphabeticalArticleList({
  items,
  onPressItem,
  emptyText,
}: {
  items: MedscapeArticleListItem[];
  onPressItem: (slug: string) => void;
  emptyText: string;
}) {
  const { colors } = useTheme();
  const scrollRef = useRef<ScrollView>(null);

  const sections = useMemo(() => groupAlphabetically(items), [items]);
  const availableLetters = useMemo(() => new Set(sections.map((s) => s.title)), [sections]);
  const offsets = useMemo(() => buildOffsets(sections), [sections]);

  const jumpTo = (letter: string) => {
    const y = offsets.get(letter);
    if (y === undefined) return;
    scrollRef.current?.scrollTo({ y, animated: true });
  };

  if (sections.length === 0) {
    return (
      <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
        {emptyText}
      </AppText>
    );
  }

  return (
    <View style={{ flex: 1, flexDirection: "row", minHeight: 0 }}>
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
              <Pressable key={article.slug} onPress={() => onPressItem(article.slug)}>
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
  );
}
