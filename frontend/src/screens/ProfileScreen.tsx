import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, ScrollView, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { HeaderMesh } from "@/components/HeaderMesh";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function ProfileScreen() {
  const { t, isFa, n, toggle: toggleLang, row } = useLang();
  const { colors, shadows, toggle: toggleTheme, isDark } = useTheme();
  const user = useAuth((s) => s.user);
  const signOut = useAuth((s) => s.signOut);
  const navigate = useNav((s) => s.navigate);

  const { data: stats } = useQuery({ queryKey: ["statistics"], queryFn: meApi.statistics });
  const { data: dash } = useQuery({ queryKey: ["dashboard"], queryFn: meApi.dashboard });

  const name = user?.profile.display_name || user?.first_name || user?.username || "";
  const initial = name.trim().charAt(0) || "؟";

  const tiles = [
    { value: n(dash?.xp ?? 0), label: t("xpLabel"), color: colors.accent, bg: colors.softBg },
    { value: n(dash?.streak_days ?? 0), label: t("streakLabel"), color: "#E08A3C", bg: "rgba(224,138,60,0.12)" },
    { value: `${n(stats?.accuracy_pct ?? 0)}%`, label: t("profileStatsAccuracy"), color: "#5AAE8C", bg: "rgba(90,174,140,0.14)" },
    { value: n(stats?.quizzes ?? 0), label: t("profileStatsQuizzes"), color: "#7E57C2", bg: "rgba(126,87,194,0.14)" },
  ];

  const Row = ({
    label,
    onPress,
    danger,
    icon,
  }: {
    label: string;
    onPress?: () => void;
    danger?: boolean;
    icon: string;
  }) => (
    <Pressable
      onPress={onPress}
      style={[
        {
          height: 52,
          borderRadius: 14,
          flexDirection: row,
          alignItems: "center",
          gap: 12,
          paddingHorizontal: 14,
          backgroundColor: danger ? "rgba(214,88,88,0.08)" : colors.cardBg,
          borderWidth: danger ? 1 : 0,
          borderColor: "rgba(214,88,88,0.2)",
        },
        !danger && shadows.raisedSm,
      ]}
    >
      <AppText size={16}>{icon}</AppText>
      <AppText weight="700" size={14} color={danger ? "#D65858" : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.appBg }}
      contentContainerStyle={{ paddingBottom: 96 }}
      showsVerticalScrollIndicator={false}
    >
      <View style={{ borderBottomLeftRadius: 28, borderBottomRightRadius: 28, overflow: "hidden" }}>
        <HeaderMesh>
          <View style={{ padding: 20, paddingBottom: 44 }}>
            <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center" }}>
              <AppText weight="800" size={17} color="#fff">
                {t("profileTitle")}
              </AppText>
              <View style={{ flexDirection: row, gap: 8, alignItems: "center" }}>
                <Pressable
                  onPress={toggleTheme}
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 15,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: "rgba(255,255,255,0.16)",
                    borderWidth: 1,
                    borderColor: "rgba(255,255,255,0.3)",
                  }}
                >
                  <AppText size={13} color="#fff">
                    {isDark ? "☀" : "☾"}
                  </AppText>
                </Pressable>
                <Pressable
                  onPress={toggleLang}
                  style={{
                    backgroundColor: "rgba(255,255,255,0.16)",
                    borderWidth: 1,
                    borderColor: "rgba(255,255,255,0.3)",
                    borderRadius: 999,
                    paddingHorizontal: 10,
                    paddingVertical: 6,
                  }}
                >
                  <AppText weight="800" size={12} color="#fff">
                    {t("langSwitch")}
                  </AppText>
                </Pressable>
              </View>
            </View>

            <View style={{ alignItems: "center", marginTop: 14 }}>
              <View
                style={{
                  width: 74,
                  height: 74,
                  borderRadius: 37,
                  backgroundColor: "rgba(255,255,255,0.16)",
                  borderWidth: 2,
                  borderColor: "rgba(255,255,255,0.35)",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <AppText weight="800" size={26} color="#fff">
                  {initial}
                </AppText>
              </View>
              <AppText weight="800" size={17} color="#fff" style={{ marginTop: 10 }}>
                {name}
              </AppText>
              <AppText weight="600" size={12} color="rgba(255,255,255,0.75)" style={{ marginTop: 2 }}>
                {user?.email}
              </AppText>
            </View>
          </View>
        </HeaderMesh>
      </View>

      <View style={{ marginHorizontal: 20, marginTop: -28 }}>
        <Card style={{ flexDirection: row, flexWrap: "wrap", gap: 10 }} raised>
          {tiles.map((tile) => (
            <View
              key={tile.label}
              style={{
                width: "47%",
                backgroundColor: tile.bg,
                borderRadius: 14,
                padding: 12,
                alignItems: "center",
              }}
            >
              <AppText weight="900" size={20} color={tile.color}>
                {tile.value}
              </AppText>
              <AppText weight="700" size={12} muted style={{ marginTop: 2 }}>
                {tile.label}
              </AppText>
            </View>
          ))}
        </Card>
      </View>

      <View style={{ paddingHorizontal: 20, paddingTop: 18, gap: 8 }}>
        <Row label={t("profileFullStats")} icon="📊" onPress={() => navigate("statistics")} />
        <Row label={t("profilePlanning")} icon="🗓" onPress={() => navigate("planning")} />
        <Row label={t("mistakesTitle")} icon="⚠️" onPress={() => navigate("mistakes")} />
        <Row label={t("profileNotifications")} icon="🔔" />
        <Row label={t("profileLogout")} icon="⎋" danger onPress={signOut} />
      </View>
    </ScrollView>
  );
}
