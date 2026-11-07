import React from "react";
import { View } from "react-native";

import { LeitnerCardField, SectionTone } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";
import { toneColors } from "@/theme/tone";

/** Matches QuizScreen's chipColors: toneColors() leaves "info" transparent,
 * meant for a full section block rather than a small tag, so it needs its
 * own visible fill/border here too. */
export function chipColors(tone: SectionTone, colors: ReturnType<typeof useTheme>["colors"]) {
  if (tone === "info") return { bg: colors.accent + "14", border: colors.accent, label: colors.accent };
  return toneColors(tone, colors);
}

/** A card's section as a small tag ("عوارض شایع"), in the section's color. */
export function SectionChip({ label, tone, onAccent }: { label: string; tone: SectionTone; onAccent?: boolean }) {
  const { colors } = useTheme();
  const tag = chipColors(tone, colors);
  return (
    <View
      style={{
        alignSelf: "center",
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 999,
        backgroundColor: onAccent ? colors.onAccentChip : tag.bg,
        borderWidth: 1,
        borderColor: onAccent ? colors.onAccentChipBorder : tag.border,
      }}
    >
      <AppText weight="800" size={12} color={onAccent ? colors.onAccent : tag.label}>
        {label}
      </AppText>
    </View>
  );
}

/** One card section on the back: a heading in the section's own color
 * (the same tone vocabulary as the lesson screen and quiz tags) over its
 * facts, each its own bulleted line. */
export function CardBackField({ block, row }: { block: LeitnerCardField; row: "row" | "row-reverse" }) {
  const { colors } = useTheme();
  const tag = chipColors(block.tone, colors);
  const items = block.items ?? block.text.split("\n").filter(Boolean);
  return (
    <View
      style={{
        backgroundColor: tag.bg,
        borderWidth: 1,
        borderColor: tag.border,
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingVertical: 9,
        gap: 4,
      }}
    >
      <View style={{ flexDirection: row, alignItems: "center", gap: 6 }}>
        <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: tag.label }} />
        <AppText weight="800" size={12.5} color={tag.label}>
          {block.label}
        </AppText>
      </View>
      {items.map((item, i) => (
        <View key={i} style={{ flexDirection: row, gap: 6 }}>
          <AppText weight="700" size={14} color={tag.label}>
            •
          </AppText>
          <AppText weight="500" size={14} style={{ flex: 1, lineHeight: 22 }}>
            {item}
          </AppText>
        </View>
      ))}
    </View>
  );
}
