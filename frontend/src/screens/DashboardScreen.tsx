import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Image, StyleSheet, useWindowDimensions, View } from "react-native";

import { meApi } from "@/api/endpoints";
import { CLINICAL_TILES, HomeTileGrid, STUDY_TILES } from "@/components/HomeTileGrid";
import { HeaderMesh } from "@/components/HeaderMesh";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { SmartSearchHomeCard } from "@/components/SmartSearchHomeCard";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { ANNOUNCEMENTS_KEY, AnnouncementBox } from "@/components/announcements/AnnouncementBox";
import { PlanSection } from "@/components/plan/PlanSection";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, spacing } from "@/theme/tokens";
import { TourTarget, useTour } from "@/tour/TourContext";

const searchOverlap = spacing.xl;
const contentWidth = { width: "100%", maxWidth: layout.contentMaxWidth, alignSelf: "center" } as const;
const headerPhoto = require("../../assets/header/home-window-light.webp");

export function DashboardScreen() {
  const { t, isFa, row } = useLang();
  const { colors, isDark } = useTheme();
  const { width } = useWindowDimensions();
  const split = width >= 850;
  const photoWidth = Math.min(width * 0.76, 680);
  const navigate = useNav((s) => s.navigate);
  const { data, isLoading, refetch, isRefetching } = useQuery({ queryKey: ["dashboard"], queryFn: meApi.dashboard });
  const queryClient = useQueryClient();
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ANNOUNCEMENTS_KEY });
    return refetch();
  };
  const replayTour = useTour("home", !isLoading);
  const hour = new Date().getHours();
  const greetKey = hour < 12 ? "greetingMorning" : hour < 18 ? "greetingAfternoon" : "greetingEvening";

  return (
    <Screen padded={false} refreshing={isRefetching} onRefresh={refresh} keyboardShouldPersistTaps="handled">
      <HeaderMesh bleedTop testID="home-header">
        <View
          testID="home-header-photo"
          pointerEvents="none"
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          aria-hidden
          style={{
            position: "absolute", top: 0, bottom: 0, width: photoWidth, overflow: "hidden",
            ...(isFa ? { left: 0 } : { right: 0, transform: [{ scaleX: -1 }] }),
          }}
        >
          <Image
            source={headerPhoto}
            resizeMode="cover"
            style={{ width: Math.max(photoWidth, 560), height: "100%", opacity: isDark ? 0.62 : 0.86 }}
          />
          <LinearGradient
            pointerEvents="none"
            colors={[`${colors.headerMesh}00`, `${colors.headerMesh}50`, colors.headerMesh]}
            locations={[0.18, 0.48, 0.88]}
            start={{ x: 0, y: 0.5 }}
            end={{ x: 1, y: 0.5 }}
            style={StyleSheet.absoluteFill}
          />
        </View>
        <View style={{
          ...contentWidth, paddingHorizontal: layout.screenPadding, paddingTop: spacing.md,
          paddingBottom: searchOverlap + spacing.lg, gap: spacing.lg,
        }}>
          <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: spacing.sm }}>
            <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm, flexShrink: 1 }}>
              <IconImage name="app-logo" size={34} />
              <AppText weight="800" size={15} color={colors.flipFrontInk} style={{ flexShrink: 1 }}>{t("appName")}</AppText>
            </View>
            <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
              <ChromeButton variant="chip" onPress={replayTour} accessibilityLabel={isFa ? "راهنمای خانه" : "Home tour"}>
                <AppText weight="800" size={13} color={colors.flipFrontInk}>?</AppText>
              </ChromeButton>
              <ThemeToggleButton variant="chip" />
              <LangToggleButton variant="chip" />
            </View>
          </View>
          <View style={{ gap: spacing.xs }}>
            <AppText accessibilityRole="header" aria-level={1} weight="900" size={24} color={colors.flipFrontInk}>
              {`${t(greetKey)} ${data?.greeting_name ?? ""}`.trim()}
            </AppText>
            <AppText size={14} color={colors.flipFrontSub}>{t("greetingSub")}</AppText>
          </View>
        </View>
      </HeaderMesh>
      <View style={{ ...contentWidth, paddingHorizontal: layout.screenPadding, marginTop: -searchOverlap, gap: spacing.lg }}>
        <SmartSearchHomeCard onPress={() => navigate("aiLab")} />
        <AnnouncementBox />
        <View style={{ flexDirection: split ? row : "column", alignItems: split ? "flex-start" : "stretch", gap: spacing.xl }}>
          <View style={{ flex: split ? 1 : undefined, minWidth: 0, gap: spacing.xl }}>
            <HomeTileGrid home title="resourceLookupQuick" rows={[CLINICAL_TILES.slice(0, 3), CLINICAL_TILES.slice(3)]} />
            <TourTarget id="home.paths"><HomeTileGrid title="pathsTitle" rows={[STUDY_TILES]} /></TourTarget>
          </View>
          <TourTarget id="home.plan" style={{ flex: split ? 1 : undefined, minWidth: 0 }}>
            <PlanSection />
          </TourTarget>
        </View>
      </View>
    </Screen>
  );
}
