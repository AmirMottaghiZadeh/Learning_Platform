import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { TextInput, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeKind } from "@/api/types";
import { AlphabeticalArticleList } from "@/components/AlphabeticalArticleList";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout, spacing } from "@/theme/tokens";

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

  const { data, isLoading } = useQuery({
    queryKey: ["medscape-articles", kind, category, specialty],
    queryFn: () => medscapeApi.bySpecialty(kind, category, specialty),
  });

  const items = data ?? [];
  const query = q.trim().toLowerCase();
  const filtered = query.length > 0 ? items.filter((a) => a.title.toLowerCase().includes(query)) : items;

  const openArticle = (slug: string) => navigate("medscapeArticle", { slug });

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

        <AlphabeticalArticleList
          items={filtered}
          onPressItem={openArticle}
          emptyText={t("medscapeNoLocalResults")}
        />
      </View>
    </Screen>
  );
}
