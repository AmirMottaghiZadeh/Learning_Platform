import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { calculatorsApi } from "@/api/endpoints";
import { CalculatorListItem } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { groupByMainCategory } from "@/utils/calculatorCategories";
import { stripHtml } from "@/utils/html";
import { specialtyIcon } from "@/utils/specialtyIcons";

/** Pure-English text, regardless of the current UI language -- a stable
 * visual badge, not a translation, so it's always built from the source
 * `name` even when the tile itself displays `name_fa`. */

function monogram(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

/** Browse-by-clinical-domain is the primary way in: a grid of the ~34 main
 * domains (matching the specialty-grid shape the disease-browse screen
 * settled on), each leading to its own CalculatorDomainScreen. Replaces the
 * previous two-level accordion-of-an-accordion (domain -> subtopic, both
 * collapsible, inline on this screen), which buried the actual calculator
 * list under two taps and made the list unscannable once a domain had more
 * than a handful of subtopics. The search box is a secondary filter over the
 * same already-fetched flat set, not a separate server query. */
export function CalculatorsScreen() {
  const { t, isFa, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["calculators"],
    queryFn: calculatorsApi.list,
  });
  const { data: categoriesData } = useQuery({
    queryKey: ["calculator-categories"],
    queryFn: calculatorsApi.categories,
  });

  const items = data ?? [];
  const allCategories = categoriesData ?? [];
  const query = q.trim().toLowerCase();

  const searchResults = useMemo(() => {
    if (query.length < 2) return null;
    return items.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        c.name_fa.includes(query) ||
        c.description.toLowerCase().includes(query) ||
        c.categories.some(
          (cat) => cat.name.toLowerCase().includes(query) || cat.name_fa.includes(query),
        ),
    );
  }, [items, query]);

  const mainGroups = useMemo(() => groupByMainCategory(items, allCategories), [items, allCategories]);

  if (isLoading) return <LoadingState />;

  return (
    <Screen>
      <ScreenChrome title={t("calculatorScreenTitle")} onBack={goBack} />
      <AppText muted weight="600" size={12} style={{ marginBottom: 14 }}>
        {items.length} {t("calculatorCountSuffix")} {t("calculatorInLabel")} {mainGroups.length}{" "}
        {t("calculatorDomainCountSuffix")}
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
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10 }}>
          {mainGroups.map((group) => {
            const total = group.subgroups.reduce((a, s) => a + s.calculators.length, 0);
            const label = isFa && group.name_fa ? group.name_fa : group.name;
            return (
              <Pressable
                key={group.id}
                onPress={() => navigate("calculatorDomain", { domainId: group.id })}
                style={{ width: "48%" }}
              >
                <View
                  style={{
                    backgroundColor: colors.cardBg,
                    borderRadius: 18,
                    borderWidth: 1,
                    borderColor: colors.border,
                    padding: 14,
                    gap: 8,
                  }}
                >
                  {specialtyIcon(group.name) ? (
                    <IconImage name={specialtyIcon(group.name)!} size={34} />
                  ) : (
                    <View
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 10,
                        backgroundColor: colors.accent + "14",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <AppText weight="800" size={11} color={colors.accent} style={{ textAlign: "left", writingDirection: "ltr" }}>
                        {monogram(group.name)}
                      </AppText>
                    </View>
                  )}
                  <AppText
                    weight="800"
                    size={12.5}
                    numberOfLines={2}
                    style={{ lineHeight: 16, textAlign: isFa ? "right" : "left", writingDirection: isFa ? "rtl" : "ltr" }}
                  >
                    {label}
                  </AppText>
                  <AppText weight="700" size={11} color={colors.muted}>
                    {total} {t("calculatorItemCountSuffix")}
                  </AppText>
                </View>
              </Pressable>
            );
          })}
        </View>
      )}
    </Screen>
  );
}

function CalculatorRow({ calc, onPress }: { calc: CalculatorListItem; onPress: () => void }) {
  const { isFa } = useLang();
  const name = isFa && calc.name_fa ? calc.name_fa : calc.name;
  const description = isFa && calc.description_fa ? calc.description_fa : calc.description;
  const dirStyle = { textAlign: isFa ? ("right" as const) : ("left" as const), writingDirection: isFa ? ("rtl" as const) : ("ltr" as const) };
  return (
    <Pressable onPress={onPress}>
      <Card style={{ gap: 4 }}>
        <AppText weight="700" size={14} style={dirStyle}>
          {stripHtml(name)}
        </AppText>
        {description ? (
          <AppText
            muted
            weight="600"
            size={12}
            numberOfLines={2}
            style={dirStyle}
          >
            {stripHtml(description)}
          </AppText>
        ) : null}
      </Card>
    </Pressable>
  );
}
