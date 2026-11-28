import React from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useLibrary } from "@/store/library";
import { useTheme } from "@/theme/ThemeProvider";

/** Saved articles moved from a full block above the list into one header chip:
 * the list and the search keep the screen, and saved items are one tap away.
 * Renders nothing when the reader has saved nothing yet. */
export function FavoritesChip({
  kind,
  open,
  onToggle,
}: {
  kind: "disease" | "guideline";
  open: boolean;
  onToggle: () => void;
}) {
  const { t, n } = useLang();
  const { colors } = useTheme();
  const count = useLibrary(
    (s) => s.favorites.filter((f) => f.source === "medscape" && f.kind === kind).length,
  );
  if (count === 0) return null;
  return (
    <Pressable
      onPress={onToggle}
      accessibilityRole="button"
      accessibilityLabel={t("favoritesTitle")}
      accessibilityState={{ selected: open }}
      hitSlop={6}
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: 5,
        minHeight: 34,
        paddingHorizontal: 11,
        borderRadius: 999,
        backgroundColor: open ? colors.accent : colors.cardBg,
        boxShadow: open ? undefined : colors.cardShadow,
      }}
    >
      <AppText size={12} color={open ? colors.onAccent : "#E0A526"}>
        ★
      </AppText>
      <AppText weight="800" size={11.5} color={open ? colors.onAccent : colors.ink}>
        {n(count)}
      </AppText>
    </Pressable>
  );
}
