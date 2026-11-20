import React from "react";
import { Text, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };

/** The three numbered heading levels (design option B): a section gets its
 * number in a filled badge, a subsection a teal "3.1" prefix, and anything
 * deeper a grey "3.1.2" prefix over a dashed rule. Article text is English,
 * so the heading always reads left to right. */
export function NumberedHeading({
  level,
  num,
  title,
  scale = 1,
}: {
  level: 1 | 2 | 3;
  num: string | null;
  title: string;
  scale?: number;
}) {
  const { colors } = useTheme();

  if (level === 1) {
    return (
      <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
        {num ? (
          <View
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              backgroundColor: colors.accent,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <AppText weight="900" size={num.length > 2 ? 13 : 16} color={colors.onAccent} center style={{ lineHeight: 20 }}>
              {num}
            </AppText>
          </View>
        ) : null}
        <AppText weight="900" size={19 * scale} style={[LTR, { flex: 1, lineHeight: Math.round(26 * scale) }]}>
          {title}
        </AppText>
      </View>
    );
  }

  if (level === 2) {
    return (
      <AppText weight="800" size={16 * scale} style={[LTR, { lineHeight: Math.round(22 * scale) }]}>
        {num ? <Text style={{ color: colors.accent }}>{num}{"  "}</Text> : null}
        {title}
      </AppText>
    );
  }

  return (
    <View
      style={{
        paddingBottom: 4,
        borderBottomWidth: 1,
        borderBottomColor: colors.trackBg,
        borderStyle: "dashed",
      }}
    >
      <AppText weight="700" size={14 * scale} color={colors.proseInk} style={[LTR, { lineHeight: Math.round(20 * scale) }]}>
        {num ? <Text style={{ color: colors.muted }}>{num}{"  "}</Text> : null}
        {title}
      </AppText>
    </View>
  );
}

/** The list-item marker (design option 6): a short vertical accent bar,
 * centred on the item's first line. Ordered lists keep their numbers. */
export function ListMarker({ lineHeight, nested = false }: { lineHeight: number; nested?: boolean }) {
  const { colors } = useTheme();
  const height = Math.round(lineHeight * 0.62);
  return (
    <View
      style={{
        width: 3,
        height,
        marginTop: (lineHeight - height) / 2,
        borderRadius: 2,
        backgroundColor: colors.accent,
        opacity: nested ? 0.55 : 1,
      }}
    />
  );
}

export type FindState = {
  /** lower-cased search term, "" when nothing is searched */
  term: string;
  /** global index of the focused match, -1 for none */
  current: number;
};

/** Splits `text` on every case-insensitive occurrence of `term` and marks
 * them, numbering matches from `start` so the one at `find.current` is the
 * focused hit. Returns the plain string untouched when nothing is searched. */
export function highlight(text: string, find: FindState, start: number, soft: string, strong: string, onStrong: string) {
  if (!find.term) return text;
  const lower = text.toLowerCase();
  const parts: React.ReactNode[] = [];
  let from = 0;
  let index = start;
  for (let hit = lower.indexOf(find.term); hit >= 0; hit = lower.indexOf(find.term, hit + find.term.length)) {
    if (hit > from) parts.push(text.slice(from, hit));
    const focused = index === find.current;
    parts.push(
      <Text
        key={hit}
        style={{ backgroundColor: focused ? strong : soft, color: focused ? onStrong : undefined, borderRadius: 2 }}
      >
        {text.slice(hit, hit + find.term.length)}
      </Text>,
    );
    index += 1;
    from = hit + find.term.length;
  }
  if (parts.length === 0) return text;
  if (from < text.length) parts.push(text.slice(from));
  return parts;
}

export function countMatches(text: string, term: string): number {
  if (!term) return 0;
  const lower = text.toLowerCase();
  let count = 0;
  for (let hit = lower.indexOf(term); hit >= 0; hit = lower.indexOf(term, hit + term.length)) count += 1;
  return count;
}
