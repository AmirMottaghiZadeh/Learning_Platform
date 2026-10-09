import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { HeaderMesh } from "@/components/HeaderMesh";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { ScreenKey } from "@/navigation/types";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing } from "@/theme/tokens";

const QUICK_ACCESS: { screen: ScreenKey; icon: IconName; labelKey: StringKey }[] = [
  { screen: "education", icon: "entry-education", labelKey: "educationLabel" },
  { screen: "guidelines", icon: "entry-guidelines", labelKey: "guidelinesLabel" },
  { screen: "diseasesConditions", icon: "entry-diseases", labelKey: "diseasesConditionsLabel" },
  { screen: "calculator", icon: "entry-calculator", labelKey: "calculatorLabel" },
];

export function DashboardScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const { toggle: toggleLang } = useLang();
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);

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
              <IconImage name="app-logo" size={34} />
              <AppText weight="800" size={15} color="#fff">
                {t("appName")}
              </AppText>
            </View>
            <View style={{ flexDirection: row, gap: 8, alignItems: "center" }}>
              <ThemeToggleButton />
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
                <IconImage name="uptodate-logo" size={36} />
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

        {/* lexicomp drug-interaction check card -- same width as UpToDate */}
        <Pressable onPress={() => navigate("lexicomp")}>
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
                <IconImage name="lexicomp-logo" size={36} />
              </View>
              <View style={{ flex: 1 }}>
                {/* Brand name -- never translated, but its alignment still
                    follows the current language like the rest of the row. */}
                <AppText weight="800" size={16}>
                  LexiComp
                </AppText>
                <AppText muted weight="600" size={12} style={{ marginTop: 3 }}>
                  {t("lexicompSub")}
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

        {/* quick-access grid: Education + the Medscape reference sections,
            as four compact tiles (2x2) */}
        <AppText weight="800" size={13} style={{ marginBottom: 10 }}>
          {t("pathsTitle")}
        </AppText>
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 10, marginBottom: spacing.xl }}>
          {QUICK_ACCESS.map((p) => (
            <Pressable
              key={p.screen}
              onPress={() => navigate(p.screen)}
              style={[
                {
                  width: "47.4%",
                  backgroundColor: colors.softBg,
                  borderRadius: 16,
                  alignItems: "center",
                  paddingVertical: 14,
                  gap: 8,
                },
                shadows.raisedSm,
              ]}
            >
              <View
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 13,
                  backgroundColor: colors.accent + "1a",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <IconImage name={p.icon} size={24} />
              </View>
              <AppText weight="800" size={12.5} center>
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

        <Pressable
          onPress={() => {
            const first = rows[0];
            if (first?.kind === "lesson" && first.atc_code) navigate("lessonList", { code: first.atc_code });
            else if (first?.kind === "mistake") setTab("profile" as any), navigate("mistakes");
            else if (rows.length > 0) setTab("flashcards" as any);
            else navigate("planning");
          }}
        >
          <Card
            style={[
              { flexDirection: row, alignItems: "center", gap: 12 },
              !isError ? { backgroundColor: colors.accent + "12", borderColor: colors.accent + "30" } : null,
            ]}
          >
            {!isError ? <IconImage name="entry-next-chapter" size={40} /> : null}
            <View style={{ flex: 1 }}>
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
                <AppText weight="700" size={13} color={colors.accent}>
                  {isFa
                    ? `شروع فصل: ${data?.next_chapter?.name_fa ?? ""} — ${n(data?.focus_session.total_minutes ?? 0)} دقیقه`
                    : `Start chapter: ${data?.next_chapter?.name_en ?? ""} — ${data?.focus_session.total_minutes ?? 0} min`}
                </AppText>
              )}
            </View>
          </Card>
        </Pressable>
      </View>
    </Screen>
  );
}
