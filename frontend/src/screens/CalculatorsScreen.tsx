import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { calculatorsApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";

/** Search-and-pick entry point into the interactive calculator library --
 * same search UX as UpToDate/Lexicomp, picking a result opens the
 * question form in CalculatorDetailScreen. */
export function CalculatorsScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());

  const { data, isFetching } = useQuery({
    queryKey: ["calculators-search", query],
    queryFn: () => calculatorsApi.list(query),
    enabled: query.length >= 2,
  });

  const rows = useMemo(() => data ?? [], [data]);

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
        {isFetching ? <AppText muted size={12}>…</AppText> : null}
      </View>

      {query.length >= 2 && rows.length === 0 && !isFetching ? (
        <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
          {t("calculatorEmptyTitle")} — {t("calculatorEmptySub")}
        </AppText>
      ) : (
        <View style={{ gap: 8 }}>
          {rows.map((calc) => (
            <Pressable key={calc.slug} onPress={() => navigate("calculatorDetail", { slug: calc.slug })}>
              <Card soft style={{ gap: 4 }}>
                <AppText weight="700" size={14} style={{ textAlign: "left", writingDirection: "ltr" }}>
                  {calc.name}
                </AppText>
                {calc.description ? (
                  <AppText
                    muted
                    weight="600"
                    size={12}
                    numberOfLines={2}
                    style={{ textAlign: "left", writingDirection: "ltr" }}
                  >
                    {calc.description}
                  </AppText>
                ) : null}
                {calc.categories.length ? (
                  <AppText
                    size={11}
                    weight="700"
                    color={colors.accent}
                    style={{ textAlign: "left", writingDirection: "ltr" }}
                  >
                    {calc.categories.join(" · ")}
                  </AppText>
                ) : null}
              </Card>
            </Pressable>
          ))}
        </View>
      )}
    </Screen>
  );
}
