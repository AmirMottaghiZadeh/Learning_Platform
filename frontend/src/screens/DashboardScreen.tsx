import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";
import Svg, { Path, Rect } from "react-native-svg";

import { meApi } from "@/api/endpoints";
import { HeaderMesh } from "@/components/HeaderMesh";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { FocusRow } from "@/api/types";
import { radius, spacing } from "@/theme/tokens";

const PATHS: { tab: string; icon: IconName; labelKey: any }[] = [
  { tab: "quiz", icon: "checklist", labelKey: "quizLabel" },
  { tab: "flashcards", icon: "mobileBlister", labelKey: "cardsLabel" },
  { tab: "lessons", icon: "openBook", labelKey: "lessonsLabel" },
  { tab: "mistakes", icon: "pillWarning", labelKey: "mistakesLabel" },
  { tab: "profile", icon: "team", labelKey: "profileLabel" },
  { tab: "statistics", icon: "chartGrowth", labelKey: "statsLabel" },
];

export function DashboardScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows, toggle: toggleTheme, isDark } = useTheme();
  const { toggle: toggleLang } = useLang();
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);
  const [focusOpen, setFocusOpen] = useState(true);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["dashboard"],
    queryFn: meApi.dashboard,
  });

  if (isLoading) return <LoadingState />;

  const hour = new Date().getHours();
  const greetKey = hour < 12 ? "greetingMorning" : hour < 18 ? "greetingAfternoon" : "greetingEvening";
  const rows = data?.focus_session.rows ?? [];

  return (
    <Screen padded={false} refreshing={isRefetching} onRefresh={refetch}>
      <HeaderMesh>
        <View style={{ padding: 20, paddingBottom: 26 }}>
          <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center" }}>
            <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
              <View
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 10,
                  backgroundColor: "#fff",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <IconImage name="mortar" size={22} />
              </View>
              <AppText weight="800" size={15} color="#fff">
                {t("appName")}
              </AppText>
            </View>
            <View style={{ flexDirection: row, gap: 8, alignItems: "center" }}>
              <Pressable
                onPress={toggleTheme}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 16,
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

          <AppText weight="900" size={22} color="#fff" style={{ marginTop: 18 }}>
            {`${t(greetKey)} ${data?.greeting_name ?? ""}`.trim()}
          </AppText>
          <AppText weight="600" size={14} color="rgba(255,255,255,0.78)" style={{ marginTop: 6, lineHeight: 25 }}>
            {t("greetingSub")}
          </AppText>
        </View>
      </HeaderMesh>

      <View style={{ padding: 20, marginTop: -14 }}>
        {/* uptodate reference card */}
        <Pressable onPress={() => navigate("uptodate")}>
          <Card style={{ marginBottom: spacing.lg }}>
            <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
              <View
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 16,
                  backgroundColor: colors.softBg,
                  borderWidth: 1,
                  borderColor: colors.trackBg,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <IconImage name="docSearch" size={34} />
              </View>
              <View style={{ flex: 1 }}>
                <View
                  style={{
                    alignSelf: "flex-start",
                    backgroundColor: colors.leitnerActiveBg,
                    borderWidth: 1,
                    borderColor: colors.trackBg,
                    borderRadius: 999,
                    paddingHorizontal: 11,
                    paddingVertical: 4,
                    marginBottom: 6,
                  }}
                >
                  <AppText weight="800" size={11} color={colors.accent}>
                    {t("uptodateBadge")}
                  </AppText>
                </View>
                <AppText weight="800" size={16}>
                  {t("uptodateTitle")}
                </AppText>
                <AppText muted weight="600" size={12} style={{ marginTop: 3 }}>
                  {t("uptodateSub")}
                </AppText>
              </View>
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 11,
                  backgroundColor: colors.accent,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <AppText weight="900" size={15} color={colors.onAccent}>
                  {isFa ? "‹" : "›"}
                </AppText>
              </View>
            </View>
          </Card>
        </Pressable>

        {/* learning paths grid */}
        <AppText weight="800" size={13} style={{ marginBottom: 10 }}>
          {t("pathsTitle")}
        </AppText>
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8, marginBottom: spacing.xl }}>
          {PATHS.map((p) => (
            <Pressable
              key={p.tab}
              onPress={() => setTab(p.tab as any)}
              style={[
                {
                  width: "31.6%",
                  backgroundColor: colors.softBg,
                  borderRadius: 16,
                  alignItems: "center",
                  paddingVertical: 12,
                },
                shadows.raisedSm,
              ]}
            >
              <IconImage name={p.icon} size={40} />
              <AppText weight="800" size={12} style={{ marginTop: 2 }}>
                {t(p.labelKey)}
              </AppText>
            </Pressable>
          ))}
        </View>

        {/* next chapter / focus session */}
        <View
          style={{
            flexDirection: row,
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 8,
          }}
        >
          <AppText weight="800" size={13}>
            {t("nextChapterTitle")}
          </AppText>
          <Pressable onPress={() => navigate("planning")}>
            <AppText weight="800" size={12} color={colors.accent}>
              {t("editPlan")}
            </AppText>
          </Pressable>
        </View>

        <Card>
          {isError ? (
            <AppText weight="700" color={colors.denyLabel}>
              {t("loadFailed")}
            </AppText>
          ) : rows.length === 0 ? (
            <AppText muted weight="600" size={13}>
              {data?.next_chapter
                ? (isFa ? data.next_chapter.name_fa : data.next_chapter.name_en)
                : t("mistakesEmptySub")}
            </AppText>
          ) : (
            <>
              <Pressable
                onPress={() => setFocusOpen((v) => !v)}
                style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}
              >
                <View style={{ flexDirection: row, alignItems: "center", gap: 9, flex: 1 }}>
                  <View
                    style={{
                      width: 34,
                      height: 34,
                      borderRadius: 11,
                      backgroundColor: colors.softBg,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Svg width={15} height={15} viewBox="0 0 24 24">
                      <Rect x={4} y={4} width={16} height={16} rx={3} stroke={colors.accent} strokeWidth={2} fill="none" />
                    </Svg>
                  </View>
                  <View style={{ flex: 1 }}>
                    <AppText weight="800" size={13}>
                      {t("nextChapterHead")}
                    </AppText>
                    <AppText muted weight="600" size={11} style={{ marginTop: 1 }}>
                      {n(data?.focus_session.total_minutes ?? 0)} {isFa ? "دقیقه" : "min"}
                    </AppText>
                  </View>
                </View>
                <AppText muted size={12} weight="800">
                  {focusOpen ? "▲" : "▼"}
                </AppText>
              </Pressable>

              {focusOpen ? (
                <View style={{ marginTop: 13, gap: 8 }}>
                  {rows.map((r, i) => (
                    <FocusRowItem key={`${r.kind}-${i}`} item={r} />
                  ))}
                  <Pressable
                    onPress={() => {
                      const first = rows[0];
                      if (first?.kind === "lesson" && first.atc_code) navigate("lessonList", { code: first.atc_code });
                      else if (first?.kind === "mistake") setTab("profile" as any), navigate("mistakes");
                      else setTab("flashcards" as any);
                    }}
                    style={{
                      backgroundColor: colors.accent,
                      borderRadius: 13,
                      paddingVertical: 13,
                      alignItems: "center",
                      marginTop: 4,
                    }}
                  >
                    <AppText weight="900" size={13} color={colors.onAccent}>
                      {isFa
                        ? `شروع جلسه — ${n(data?.focus_session.total_minutes ?? 0)} دقیقه`
                        : `Start session — ${data?.focus_session.total_minutes ?? 0} min`}
                    </AppText>
                  </Pressable>
                </View>
              ) : null}
            </>
          )}
        </Card>
      </View>
    </Screen>
  );
}

function FocusRowItem({ item }: { item: FocusRow }) {
  const { colors } = useTheme();
  const { isFa, n, row } = useLang();
  const tint =
    item.kind === "mistake" ? colors.denyBg : item.kind === "leitner" ? colors.leitnerActiveBg : colors.softBg;
  const min =
    item.kind === "mistake" ? colors.denyLabel : colors.accent;
  return (
    <View
      style={{
        flexDirection: row,
        alignItems: "center",
        gap: 11,
        backgroundColor: tint,
        borderRadius: 13,
        padding: 11,
      }}
    >
      <View style={{ flex: 1 }}>
        <AppText weight="800" size={12.5}>
          {isFa ? item.title_fa : item.title_en}
        </AppText>
        <AppText muted weight="600" size={11} style={{ marginTop: 1 }}>
          {isFa ? item.sub_fa : item.sub_en}
        </AppText>
      </View>
      <AppText weight="900" size={11} color={min}>
        {n(item.minutes)} {isFa ? "دقیقه" : "min"}
      </AppText>
    </View>
  );
}
