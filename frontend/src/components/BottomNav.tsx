import React from "react";
import { Pressable, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget } from "@/tour/TourContext";
import { layout } from "@/theme/tokens";
import { LOCKED_TABS, TAB_ORDER, TabKey } from "@/navigation/types";
import { AppText } from "./primitives/AppText";
import { IconImage, IconName } from "./primitives/IconImage";

/** How much room to leave under a screen's content so its end isn't hidden
 * behind the tab bar -- which grows by the home-indicator strip (see
 * BottomNav) -- plus `extra` breathing space. */
export function useNavClearance(extra = 0) {
  return layout.bottomNavHeight + useSafeAreaInsets().bottom + extra;
}

const TAB_META: Record<
  TabKey,
  { icon: IconName; labelKey: "navHome" | "lessonsLabel" | "profileLabel" }
> = {
  dashboard: { icon: "nav-home", labelKey: "navHome" },
  lessons: { icon: "nav-lessons", labelKey: "lessonsLabel" },
  profile: { icon: "nav-profile", labelKey: "profileLabel" },
};

// Which top-level screens count as "inside" which tab.
const SCREEN_TO_TAB: Record<string, TabKey> = {
  dashboard: "dashboard",
  lessons: "lessons",
  lessonList: "lessons",
  lessonDetail: "lessons",
  quiz: "lessons",
  profile: "profile",
  mistakes: "profile",
  statistics: "profile",
  planning: "profile",
  planningSetup: "profile",
  settings: "profile",
  plans: "profile",
  devices: "profile",
  notifications: "profile",
  downloads: "profile",
  support: "profile",
  uptodate: "dashboard",
  uptodateOutline: "dashboard",
  uptodateArticle: "dashboard",
  lexicomp: "dashboard",
  education: "lessons",
  guidelines: "dashboard",
  diseasesConditions: "dashboard",
  medscapeOutline: "dashboard",
  medscapeArticle: "dashboard",
  calculator: "dashboard",
  calculatorDomain: "dashboard",
  calculatorDetail: "dashboard",
};

export function BottomNav() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const { t, isFa } = useLang();
  const screen = useNav((s) => s.screen);
  const setTab = useNav((s) => s.setTab);
  const activeTab = SCREEN_TO_TAB[screen] ?? "dashboard";
  return (
    // The guided tours point at the bar as "nav".
    <TourTarget
      id="nav"
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        // Grows down over the home indicator (iPhone) / gesture bar so the
        // bar runs to the bottom edge with its tabs clear of it.
        height: layout.bottomNavHeight + insets.bottom,
      }}
    >
    <View
      role="navigation"
      accessibilityLabel={isFa ? "ناوبری اصلی" : "Main navigation"}
      style={{
        flex: 1,
        backgroundColor: colors.cardBg,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        flexDirection: isFa ? "row-reverse" : "row",
        alignItems: "center",
        paddingBottom: 6 + insets.bottom,
      }}
    >
      {TAB_ORDER.map((tab) => {
        const meta = TAB_META[tab];
        const isActive = tab === activeTab;
        const locked = LOCKED_TABS.includes(tab);
        return (
          <Pressable
            key={tab}
            accessibilityRole="button"
            aria-current={isActive ? "page" : undefined}
            accessibilityState={{ selected: isActive }}
            onPress={() => setTab(tab)}
            style={({ pressed }) => ({ flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center", opacity: pressed ? 0.75 : 1 })}
          >
            <View style={{ alignItems: "center", justifyContent: "center", width: 52, height: 28, borderRadius: 10,
              backgroundColor: isActive ? colors.leitnerActiveBg : "transparent", opacity: isActive ? 1 : 0.65 }}>
              <IconImage name={meta.icon} size={24} />
              {locked ? (
                <View
                  style={{
                    position: "absolute",
                    top: -3,
                    ...(isFa ? { left: -5 } : { right: -5 }),
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: colors.cautLabel,
                    borderWidth: 1.5,
                    borderColor: colors.navBg,
                  }}
                />
              ) : null}
            </View>
            <AppText
              size={12}
              weight={isActive ? "700" : "500"}
              color={isActive ? colors.accent : colors.muted}
            >
              {t(meta.labelKey)}
            </AppText>
          </Pressable>
        );
      })}
    </View>
    </TourTarget>
  );
}
