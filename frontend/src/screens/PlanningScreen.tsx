import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { DAY_LABELS_FULL } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function PlanningScreen() {
  const { t, lang } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({ queryKey: ["plan"], queryFn: meApi.plan });
  const [days, setDays] = useState<boolean[]>([false, false, false, false, false, false, false]);
  const [reminders, setReminders] = useState(false);

  useEffect(() => {
    if (data) {
      setDays(data.days);
      setReminders(data.reminders_enabled);
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () => meApi.savePlan({ days, reminders_enabled: reminders }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plan"] });
      goBack();
    },
  });

  if (isLoading) return <LoadingState />;

  const labels = DAY_LABELS_FULL[lang];

  return (
    <Screen>
      <ScreenChrome title={t("planningTitle")} onBack={goBack} help="planning" />
      <AppText muted weight="600" size={13} style={{ marginBottom: spacing.md }}>
        {t("planningSub")}
      </AppText>

      <View style={{ gap: 8, marginBottom: spacing.lg }}>
        {labels.map((label, i) => {
          const on = days[i];
          return (
            <Pressable
              key={i}
              onPress={() => setDays((d) => d.map((v, j) => (j === i ? !v : v)))}
              style={{
                flexDirection: "row",
                alignItems: "center",
                gap: 12,
                height: 50,
                paddingHorizontal: 16,
                borderRadius: 14,
                backgroundColor: on ? colors.accent + "1a" : colors.softBg,
                borderWidth: 1.5,
                borderColor: on ? colors.accent : colors.trackBg,
              }}
            >
              <View
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  backgroundColor: on ? colors.accent : "transparent",
                  borderWidth: on ? 0 : 1.5,
                  borderColor: colors.trackBg,
                }}
              />
              <AppText weight="700" size={14} color={on ? colors.accent : colors.ink}>
                {label}
              </AppText>
            </Pressable>
          );
        })}
      </View>

      <Pressable
        onPress={() => setReminders((v) => !v)}
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          height: 48,
          paddingHorizontal: 16,
          borderRadius: 14,
          backgroundColor: colors.softBg,
          marginBottom: spacing.lg,
        }}
      >
        <AppText weight="700" size={14}>
          {t("profileNotifications")}
        </AppText>
        <View
          style={{
            width: 44,
            height: 26,
            borderRadius: 13,
            backgroundColor: reminders ? colors.accent : colors.trackBg,
            padding: 3,
            alignItems: reminders ? "flex-end" : "flex-start",
          }}
        >
          <View style={{ width: 20, height: 20, borderRadius: 10, backgroundColor: "#fff" }} />
        </View>
      </Pressable>

      <Pressable
        onPress={() => save.mutate()}
        style={{
          height: 50,
          borderRadius: 14,
          backgroundColor: colors.accent,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <AppText weight="800" size={15} color={colors.onAccent}>
          {t("planningSave")}
        </AppText>
      </Pressable>
    </Screen>
  );
}
