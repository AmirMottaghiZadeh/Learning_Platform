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
import { CalculatorMainGroup, groupByMainCategory } from "@/utils/calculatorCategories";
import { stripHtml } from "@/utils/html";

/** Browse-by-clinical-domain is the primary way in, two levels deep (domain
 * -> subtopic -> calculator) -- matching the source snapshot's own taxonomy
 * rather than one flat list of ~170 tags. The search box is a secondary
 * filter over the same already-fetched set, not a separate server query. */
export function CalculatorsScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const [openMain, setOpenMain] = useState<string | null>(null);
  const [openSub, setOpenSub] = useState<string | null>(null);

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

  const mainGroups = useMemo(() => groupByMainCategory(items), [items]);

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
          {mainGroups.map((group) => (
            <MainGroupCard
              key={group.name}
              group={group}
              isOpen={openMain === group.name}
              onToggle={() => {
                setOpenMain(openMain === group.name ? null : group.name);
                setOpenSub(null);
              }}
              openSub={openSub}
              onToggleSub={(name) => setOpenSub((cur) => (cur === name ? null : name))}
              onPickCalculator={(slug) => navigate("calculatorDetail", { slug })}
            />
          ))}
        </View>
      )}
    </Screen>
  );
}

function MainGroupCard({
  group,
  isOpen,
  onToggle,
  openSub,
  onToggleSub,
  onPickCalculator,
}: {
  group: CalculatorMainGroup;
  isOpen: boolean;
  onToggle: () => void;
  openSub: string | null;
  onToggleSub: (name: string) => void;
  onPickCalculator: (slug: string) => void;
}) {
  const { colors } = useTheme();
  const { row } = useLang();
  const total = group.subgroups.reduce((a, s) => a + s.calculators.length, 0);

  return (
    <View
      style={{
        backgroundColor: colors.cardBg,
        borderRadius: 14,
        borderWidth: 1,
        borderColor: colors.border,
        overflow: "hidden",
      }}
    >
      <Pressable
        onPress={onToggle}
        style={{ padding: 13, flexDirection: row, alignItems: "center", justifyContent: "space-between" }}
      >
        <AppText weight="800" size={13}>
          {group.name}
        </AppText>
        <AppText muted weight="700" size={12}>
          {total} {isOpen ? "▲" : "▼"}
        </AppText>
      </Pressable>

      {isOpen ? (
        <View style={{ paddingHorizontal: 10, paddingBottom: 10, gap: 6 }}>
          {group.subgroups.map((sub) => (
            <View
              key={sub.name}
              style={{
                backgroundColor: colors.softBg,
                borderRadius: 12,
                borderWidth: 1,
                borderColor: colors.trackBg,
                overflow: "hidden",
              }}
            >
              <Pressable
                onPress={() => onToggleSub(sub.name)}
                style={{ padding: 11, flexDirection: row, alignItems: "center", justifyContent: "space-between" }}
              >
                <AppText weight="700" size={12.5}>
                  {sub.name}
                </AppText>
                <AppText muted weight="700" size={11.5}>
                  {sub.calculators.length} {openSub === sub.name ? "▲" : "▼"}
                </AppText>
              </Pressable>
              {openSub === sub.name ? (
                <View style={{ paddingHorizontal: 8, paddingBottom: 8, gap: 6 }}>
                  {sub.calculators.map((calc) => (
                    <CalculatorRow key={calc.slug} calc={calc} onPress={() => onPickCalculator(calc.slug)} />
                  ))}
                </View>
              ) : null}
            </View>
          ))}
        </View>
      ) : null}
    </View>
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
