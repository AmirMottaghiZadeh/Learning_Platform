import React from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

/** Two letters for a topic tile: first letters of its alphabetic words, so
 * "Allergy & Immunology" reads AI rather than A&. */
export function topicMonogram(name: string): string {
  const letters = name
    .split(/\s+/)
    .filter((word) => /^[A-Za-z]/.test(word))
    .map((word) => word[0]);
  return (letters.slice(0, 2).join("") || name.slice(0, 2)).toUpperCase();
}

/** One topic in the horizontal rail above an article list: monogram, name and
 * article count. The card carries the count, not the list header, so a reader
 * can pick a topic without scrolling. */
export function TopicCard({
  name,
  count,
  active = false,
  onPress,
  countLabel,
}: {
  name: string;
  count: number;
  active?: boolean;
  onPress: () => void;
  countLabel: string;
}) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${name}, ${count} ${countLabel}`}
      style={{ width: 134 }}
    >
      <View
        style={{
          backgroundColor: active ? colors.accent : colors.cardBg,
          borderRadius: 16,
          padding: 12,
          minHeight: 96,
          gap: 8,
          borderWidth: 1,
          borderColor: active ? colors.accent : "transparent",
          boxShadow: active ? undefined : colors.cardShadow,
        }}
      >
        <View
          style={{
            width: 30,
            height: 30,
            borderRadius: 9,
            backgroundColor: active ? colors.onAccentChip : colors.accent + "14",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AppText
            weight="800"
            size={11}
            color={active ? colors.onAccent : colors.accent}
            style={{ fontFamily: fontFamily("800") }}
          >
            {topicMonogram(name)}
          </AppText>
        </View>
        <AppText
          weight="800"
          size={12}
          numberOfLines={2}
          color={active ? colors.onAccent : colors.ink}
          style={{ lineHeight: 16, textAlign: "left", writingDirection: "ltr" }}
        >
          {name}
        </AppText>
        <AppText
          weight="700"
          size={10}
          color={active ? colors.onAccentSub : colors.muted}
          style={{ textAlign: "left", writingDirection: "ltr", marginTop: "auto" }}
        >
          {count} {countLabel}
        </AppText>
      </View>
    </Pressable>
  );
}
