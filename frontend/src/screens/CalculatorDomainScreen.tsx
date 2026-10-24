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
import { groupByMainCategory } from "@/utils/calculatorCategories";
import { stripHtml } from "@/utils/html";

/** One clinical domain's calculators, grouped by its real subtopics -- every
 * subtopic section always open (no accordion-of-an-accordion), replacing the
 * nested-collapse UX the domain grid in CalculatorsScreen used to lead into.
 * A big domain (Cardiology: 227 calculators, 23 subtopics) is still a long
 * scroll, but the clinical grouping stays legible the whole way down, which
 * an A-Z list (the disease-browse screen's shape) would throw away here --
 * unlike disease specialties, a calculator's subtopic is a real, meaningful
 * clinical grouping, not an arbitrary bucket. */
export function CalculatorDomainScreen() {
  const { t, isFa, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const domainId = Number(useNav((s) => s.params.domainId ?? NaN));

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
  const group = useMemo(
    () => groupByMainCategory(items, allCategories).find((g) => g.id === domainId) ?? null,
    [items, allCategories, domainId],
  );
  const total = group?.subgroups.reduce((a, s) => a + s.calculators.length, 0) ?? 0;
  const title = group ? (isFa && group.name_fa ? group.name_fa : group.name) : "";

  const query = q.trim().toLowerCase();
  const filtered = useMemo(() => {
    if (!group) return [];
    if (query.length === 0) return group.subgroups;
    return group.subgroups
      .map((sub) => ({
        ...sub,
        calculators: sub.calculators.filter(
          (c) => c.name.toLowerCase().includes(query) || c.name_fa.includes(query),
        ),
      }))
      .filter((sub) => sub.calculators.length > 0);
  }, [group, query]);

  const openCalculator = (slug: string) => navigate("calculatorDetail", { slug });

  if (isLoading) return <LoadingState />;

  return (
    <Screen>
      <ScreenChrome title={title} onBack={goBack} />
      <AppText muted weight="600" size={12} style={{ marginBottom: 14 }}>
        {total} {t("calculatorCountSuffix")} {t("calculatorInLabel")} {group?.subgroups.length ?? 0}{" "}
        {t("calculatorSubtopicCountSuffix")}
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

      {filtered.length === 0 ? (
        <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
          {t("calculatorEmptyTitle")} — {t("calculatorEmptySub")}
        </AppText>
      ) : (
        <View style={{ gap: 18 }}>
          {filtered.map((sub) => (
            <View key={sub.id} style={{ gap: 8 }}>
              <View
                style={{
                  flexDirection: row,
                  alignItems: "center",
                  gap: 8,
                  backgroundColor: colors.accent + "14",
                  borderRadius: 10,
                  paddingHorizontal: 12,
                  paddingVertical: 7,
                }}
              >
                <View style={{ width: 4, height: 14, borderRadius: 3, backgroundColor: colors.accent }} />
                <AppText
                  weight="800"
                  size={12.5}
                  color={colors.accent}
                  style={{ textAlign: isFa ? "right" : "left", writingDirection: isFa ? "rtl" : "ltr" }}
                >
                  {isFa && sub.name_fa ? sub.name_fa : sub.name}
                </AppText>
              </View>
              <View style={{ gap: 8 }}>
                {sub.calculators.map((calc) => (
                  <CalculatorRow key={calc.slug} calc={calc} onPress={() => openCalculator(calc.slug)} />
                ))}
              </View>
            </View>
          ))}
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
          <AppText muted weight="600" size={12} numberOfLines={2} style={dirStyle}>
            {stripHtml(description)}
          </AppText>
        ) : null}
      </Card>
    </Pressable>
  );
}
