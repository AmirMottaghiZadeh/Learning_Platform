import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { meApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_SHORT } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function StatisticsScreen() {
  const { t, lang, n } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ["statistics"],
    queryFn: meApi.statistics,
  });

  if (isLoading) return <LoadingState />;

  const acc = data?.accuracy_pct ?? 0;
  const R = 40;
  const C = 2 * Math.PI * R;
  const bars = data?.week_bars ?? [0, 0, 0, 0, 0, 0, 0];
  const maxBar = Math.max(1, ...bars);
  const days = DAY_LABELS_SHORT[lang];

  return (
    <Screen refreshing={isRefetching} onRefresh={refetch}>
      <ScreenChrome title={t("statsTitle")} onBack={goBack} help="statistics" />

      <Card raised style={{ flexDirection: "row", alignItems: "center", gap: 16, marginBottom: spacing.lg }}>
        <Svg width={96} height={96} viewBox="0 0 96 96">
          <Circle cx={48} cy={48} r={R} fill="none" stroke={colors.trackBg} strokeWidth={10} />
          <Circle
            cx={48}
            cy={48}
            r={R}
            fill="none"
            stroke={colors.accent}
            strokeWidth={10}
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - acc / 100)}
            transform="rotate(-90 48 48)"
          />
        </Svg>
        <View>
          <AppText weight="900" size={24}>
            {n(acc)}%
          </AppText>
          <AppText weight="700" size={12} muted style={{ marginTop: 3 }}>
            {t("statsAccuracy")}
          </AppText>
        </View>
      </Card>

      <Card style={{ marginBottom: spacing.lg }}>
        <AppText weight="800" size={13} style={{ marginBottom: 12 }}>
          {t("statsWeek")}
        </AppText>
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8, height: 96 }}>
          {bars.map((v, i) => (
            <View key={i} style={{ flex: 1, alignItems: "center", justifyContent: "flex-end", gap: 6, height: "100%" }}>
              <View
                style={{
                  width: "100%",
                  borderRadius: 6,
                  backgroundColor: colors.accent,
                  height: `${Math.max(4, (v / maxBar) * 100)}%`,
                }}
              />
              <AppText weight="700" size={12} muted>
                {days[i]}
              </AppText>
            </View>
          ))}
        </View>
      </Card>

      <View style={{ flexDirection: "row", gap: 8 }}>
        <StatTile value={n(data?.quizzes ?? 0)} label={t("statsQuizzes")} />
        <StatTile value={n(data?.reviews ?? 0)} label={t("statsReviews")} />
        <StatTile value={n(data?.minutes ?? 0)} label={t("statsMinutes")} />
      </View>
    </Screen>
  );
}

function StatTile({ value, label }: { value: string; label: string }) {
  return (
    <Card style={{ flex: 1, alignItems: "center" }}>
      <AppText weight="900" size={17}>
        {value}
      </AppText>
      <AppText weight="700" size={12} muted center style={{ marginTop: 3 }}>
        {label}
      </AppText>
    </Card>
  );
}
