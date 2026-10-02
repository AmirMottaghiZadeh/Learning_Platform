import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { calculatorsApi } from "@/api/endpoints";
import { CalculatorListItem } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { groupByCategory } from "@/utils/calculatorCategories";
import { stripHtml } from "@/utils/html";

/** Browse-by-clinical-category is the primary way in (matching how the
 * source organizes its ~500 calculators) -- the search box is a secondary
 * filter over the same already-fetched set, not a separate server query. */
export function CalculatorsScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const [openCategory, setOpenCategory] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["calculators"],
    queryFn: calculatorsApi.list,
  });

  const items = data ?? [];
  const query = q.trim().toLowerCase();

  const searchResults = useMemo(() => {
    if (query.length < 2) return null;
    return items.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        c.description.toLowerCase().includes(query) ||
        c.categories.some((cat) => cat.toLowerCase().includes(query)),
    );
  }, [items, query]);

  const categories = useMemo(() => groupByCategory(items), [items]);

  if (isLoading) return <LoadingState />;

  return (
    <Screen>
      <ScreenChrome title={t("calculatorScreenTitle")} onBack={goBack} />
      <AppText muted weight="600" size={12} style={{ marginBottom: 14 }}>
        {t("calculatorSourceNote")}
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
          marginBottom: spacing.lg,
        }}
      >
        <AppText muted>⌕</AppText>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder={t("calculatorSearchPlaceholder")}
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

      {searchResults ? (
        searchResults.length === 0 ? (
          <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
            {t("calculatorEmptyTitle")} — {t("calculatorEmptySub")}
          </AppText>
        ) : (
          <View style={{ gap: 8 }}>
            {searchResults.map((calc) => (
              <CalculatorRow key={calc.slug} calc={calc} onPress={() => navigate("calculatorDetail", { slug: calc.slug })} />
            ))}
          </View>
        )
      ) : (
        <View style={{ gap: 8 }}>
          {categories.map((category) => (
            <View
              key={category.name}
              style={{
                backgroundColor: colors.cardBg,
                borderRadius: 14,
                borderWidth: 1,
                borderColor: colors.border,
                overflow: "hidden",
              }}
            >
              <Pressable
                onPress={() => setOpenCategory(openCategory === category.name ? null : category.name)}
                style={{
                  padding: 13,
                  flexDirection: row,
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <AppText weight="800" size={13}>
                  {category.name}
                </AppText>
                <AppText muted weight="700" size={12}>
                  {category.calculators.length} {openCategory === category.name ? "▲" : "▼"}
                </AppText>
              </Pressable>

              {openCategory === category.name ? (
                <View style={{ paddingHorizontal: 10, paddingBottom: 10, gap: 6 }}>
                  {category.calculators.map((calc) => (
                    <CalculatorRow
                      key={calc.slug}
                      calc={calc}
                      soft
                      onPress={() => navigate("calculatorDetail", { slug: calc.slug })}
                    />
                  ))}
                </View>
              ) : null}
            </View>
          ))}
        </View>
      )}
    </Screen>
  );
}

function CalculatorRow({
  calc,
  onPress,
  soft,
}: {
  calc: CalculatorListItem;
  onPress: () => void;
  soft?: boolean;
}) {
  return (
    <Pressable onPress={onPress}>
      <Card soft={soft} style={{ gap: 4 }}>
        <AppText weight="700" size={14} style={{ textAlign: "left", writingDirection: "ltr" }}>
          {stripHtml(calc.name)}
        </AppText>
        {calc.description ? (
          <AppText
            muted
            weight="600"
            size={12}
            numberOfLines={2}
            style={{ textAlign: "left", writingDirection: "ltr" }}
          >
            {stripHtml(calc.description)}
          </AppText>
        ) : null}
      </Card>
    </Pressable>
  );
}
