import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { ScreenKey } from "@/navigation/types";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { TourTarget } from "@/tour/TourContext";

type Tile = { label: StringKey; icon: IconName | "algorithms"; screen?: ScreenKey };

export const CLINICAL_TILES: Tile[] = [
  { label: "tileUptodate", icon: "uptodate-logo", screen: "uptodate" },
  { label: "tileLexicomp", icon: "lexicomp-logo", screen: "lexicomp" },
  { label: "tileDiseases", icon: "entry-diseases", screen: "diseasesConditions" },
  { label: "tileGuidelines", icon: "entry-guidelines", screen: "guidelines" },
  { label: "tileCalculator", icon: "entry-calculator", screen: "calculator" },
  { label: "tileAlgorithms", icon: "algorithms" },
];

export const STUDY_TILES: Tile[] = [
  { label: "lessonsLabel", icon: "edu-lessons", screen: "lessons" },
  { label: "quizLabel", icon: "edu-quiz", screen: "quiz" },
  { label: "tileFlashcards", icon: "edu-flashcards" },
];

export function HomeTileGrid({ title, rows, home = false }: { title: StringKey; rows: Tile[][]; home?: boolean }) {
  const { row, t } = useLang();
  const { colors } = useTheme();
  const navigate = useNav((s) => s.navigate);
  return (
    <View style={{ gap: spacing.sm }}>
      <AppText accessibilityRole="header" aria-level={2} size={18} weight="800">{t(title)}</AppText>
      {rows.map((tiles) => (
        <View key={tiles[0].label} style={{ flexDirection: row, gap: spacing.sm, alignItems: "stretch" }}>
          {tiles.map(({ label, screen, icon }) => {
            const coming = !screen;
            const copy = t(label);
            return (
              <TourTarget key={label} id={home && screen ? `home.${screen}` : `tile.${label}`} style={{ flex: 1, minWidth: 0 }}>
                <Pressable
                  testID={`tile-${label}`}
                  accessibilityRole="button"
                  accessibilityLabel={coming ? `${copy} · ${t("comingSoon")}` : copy}
                  accessibilityState={{ disabled: coming }}
                  disabled={coming}
                  onPress={screen ? () => navigate(screen) : undefined}
                  style={({ pressed }) => ({ flex: 1, opacity: pressed ? 0.76 : 1 })}
                >
                  <Card soft={coming} padded={false} style={{
                    aspectRatio: 1, flex: 1, minHeight: 86,
                    justifyContent: "center", alignItems: "center", gap: 5, paddingHorizontal: 4, paddingVertical: 6,
                  }}>
                    {icon === "algorithms" ? (
                      <Svg width={29} height={29} viewBox="0 0 24 24" fill="none" stroke={coming ? colors.muted : colors.accent} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <Path d="M10 3h4v4h-4z M4 17h4v4H4z M16 17h4v4h-4z M12 7v5m-6 5v-5h12v5" />
                      </Svg>
                    ) : <IconImage name={icon} size={30} />}
                    <AppText center size={12} weight="800" muted={coming} style={{ width: "100%", lineHeight: 18 }}>{copy}</AppText>
                    {coming ? <AppText center muted size={10} style={{ lineHeight: 13 }}>{t("comingSoon")}</AppText> : null}
                  </Card>
                </Pressable>
              </TourTarget>
            );
          })}
        </View>
      ))}
    </View>
  );
}
