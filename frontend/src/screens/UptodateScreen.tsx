import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { ApiError } from "@/api/client";
import { uptodateApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";

export function UptodateScreen() {
  const { t, isFa, n, row: rowDir } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());

  const { data, isFetching, error } = useQuery({
    queryKey: ["uptodate-search", query],
    queryFn: () => uptodateApi.search(query),
    enabled: query.length >= 2,
    retry: false,
  });

  const locked = error instanceof ApiError && error.status === 503;
  const rows = useMemo(() => data ?? [], [data]);

  return (
    <Screen>
      <ScreenChrome title={t("uptodateScreenTitle")} onBack={goBack} />
      <AppText muted weight="600" size={12} style={{ marginBottom: 14 }}>
        {t("uptodateSourceNote")}
      </AppText>

      <View
        style={{
          flexDirection: rowDir,
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
          placeholder={t("uptodateSearchPlaceholder")}
          placeholderTextColor={colors.muted}
          style={{
            flex: 1,
            fontFamily: fontFamily("600"),
            fontSize: 13,
            color: colors.ink,
            textAlign: isFa ? "right" : "left",
            padding: 0,
          }}
        />
        {isFetching ? <AppText muted size={12}>…</AppText> : null}
      </View>

      {locked ? (
        <Card>
          <AppText weight="800" size={15} color={colors.accent}>
            {t("comingSoon")}
          </AppText>
          <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
            {t("lockedFeature")}
          </AppText>
        </Card>
      ) : query.length >= 2 && rows.length === 0 && !isFetching ? (
        <View style={{ alignItems: "center", paddingVertical: 40 }}>
          <View
            style={{
              width: 60,
              height: 60,
              borderRadius: 18,
              backgroundColor: colors.softBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 14,
            }}
          >
            <IconImage name="docSearch" size={34} />
          </View>
          <AppText weight="800" size={15}>
            {t("uptodateEmptyTitle")}
          </AppText>
          <AppText muted weight="600" size={13} center style={{ marginTop: 8, lineHeight: 22 }}>
            {t("uptodateEmptySub")}
          </AppText>
        </View>
      ) : (
        <View style={{ gap: 10 }}>
          {rows.map((row) => (
            <Pressable
              key={row.id}
              onPress={() => navigate("uptodateOutline", { id: row.id, title: row.title })}
            >
              <Card style={{ flexDirection: rowDir, alignItems: "center", gap: 12 }}>
                <View
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 12,
                    backgroundColor: colors.softBg,
                    borderWidth: 1,
                    borderColor: colors.trackBg,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <IconImage name="docSearch" size={24} />
                </View>
                <View style={{ flex: 1 }}>
                  <AppText weight="800" size={14} style={{ lineHeight: 21 }}>
                    {row.title}
                  </AppText>
                  {row.section ? (
                    <AppText muted weight="600" size={12} style={{ marginTop: 3 }}>
                      {row.section}
                    </AppText>
                  ) : null}
                </View>
                <AppText muted size={13}>
                  {isFa ? "‹" : "›"}
                </AppText>
              </Card>
            </Pressable>
          ))}
        </View>
      )}
    </Screen>
  );
}
