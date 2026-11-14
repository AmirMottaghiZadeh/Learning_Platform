import React from "react";
import { Pressable, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useLibrary } from "@/store/library";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

export function ReferenceFavorites({ kind }: { kind: "disease" | "guideline" }) {
  const { t } = useLang(), { colors, shadows } = useTheme();
  const favorites = useLibrary(s => s.favorites);
  const toggle = useLibrary(s => s.toggleFavorite), navigate = useNav(s => s.navigate);
  const mine = favorites.filter(f => f.source === "medscape" && f.kind === kind);
  return <View style={{ gap: 10, marginBottom: 18 }}><View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}><AppText weight="900" size={15} color="#E0A526">★</AppText><AppText weight="800" size={14}>{t("favoritesTitle")}</AppText></View>{mine.length ? mine.map(f => <Pressable key={f.id} onPress={() => navigate("medscapeOutline", { slug: f.id })} style={[{ flexDirection: "row", alignItems: "center", gap: 10, backgroundColor: colors.cardBg, borderRadius: 16, padding: 14 }, shadows.raisedSm]}><View style={{ flex: 1, gap: 4 }}>{f.section ? <AppText size={11.5} color={colors.accent} style={{ writingDirection: "ltr", textAlign: "left" }}>{f.section}</AppText> : null}<AppText weight="800" size={14.5} style={{ writingDirection: "ltr", textAlign: "left", lineHeight: 21 }}>{f.title}</AppText></View><Pressable onPress={event => { event.stopPropagation(); toggle(f); }} accessibilityLabel={t("favoriteRemove")} style={{ width: 44, height: 44, justifyContent: "center", alignItems: "center" }}><AppText size={18} color="#E0A526">★</AppText></Pressable></Pressable>) : <View style={{ backgroundColor: colors.cardBg, borderRadius: 16, padding: 16 }}><AppText muted size={13} style={{ lineHeight: 22 }}>{t("favoritesEmpty")}</AppText></View>}</View>;
}
