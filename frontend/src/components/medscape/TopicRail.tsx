import React from "react";
import { ScrollView, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { TopicCard } from "@/components/medscape/TopicCard";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export type Topic = { name: string; count: number };

/** The horizontal topic rail. Picking a card narrows the list below it; the
 * count on each card is the number of articles that topic holds, so the rail
 * doubles as an overview of where the content actually is. */
export function TopicRail({
  topics,
  active,
  onSelect,
  label,
}: {
  topics: Topic[];
  active?: string | null;
  onSelect: (name: string) => void;
  label: string;
}) {
  const { t } = useLang();
  const { colors } = useTheme();
  if (topics.length === 0) return null;
  return (
    <View style={{ gap: 8 }}>
      <AppText weight="800" size={11.5} color={colors.muted} style={{ letterSpacing: 0.3 }}>
        {label}
      </AppText>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 10, paddingHorizontal: 2, paddingBottom: 4 }}
      >
        {topics.map((topic) => (
          <TopicCard
            key={topic.name}
            name={topic.name}
            count={topic.count}
            active={topic.name === active}
            onPress={() => onSelect(topic.name)}
            countLabel={t("medscapeArticleCount")}
          />
        ))}
      </ScrollView>
    </View>
  );
}
