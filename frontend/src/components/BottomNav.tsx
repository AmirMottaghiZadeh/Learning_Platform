import React, { useEffect, useRef, useState } from "react";
import { Animated, LayoutChangeEvent, Pressable, View } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";
import { LOCKED_TABS, TAB_ORDER, TabKey } from "@/navigation/types";
import { AppText } from "./primitives/AppText";
import { IconImage, IconName } from "./primitives/IconImage";

const PILL_W = 56;

const TAB_META: Record<
  TabKey,
  { icon: IconName; labelKey: "navHome" | "lessonsLabel" | "cardsLabel" | "quizLabel" | "profileLabel" }
> = {
  dashboard: { icon: "phoneHealth", labelKey: "navHome" },
  lessons: { icon: "openBook", labelKey: "lessonsLabel" },
  flashcards: { icon: "mobileBlister", labelKey: "cardsLabel" },
  quiz: { icon: "checklist", labelKey: "quizLabel" },
  profile: { icon: "team", labelKey: "profileLabel" },
};

// Which top-level screens count as "inside" which tab.
const SCREEN_TO_TAB: Record<string, TabKey> = {
  dashboard: "dashboard",
  lessons: "lessons",
  lessonList: "lessons",
  lessonDetail: "lessons",
  flashcards: "flashcards",
  quiz: "quiz",
  profile: "profile",
  mistakes: "profile",
  statistics: "profile",
  planning: "profile",
  uptodate: "dashboard",
  uptodateArticle: "dashboard",
};

export function BottomNav() {
  const { colors, isDark } = useTheme();
  const { t, isFa } = useLang();
  const screen = useNav((s) => s.screen);
  const setTab = useNav((s) => s.setTab);
  const activeTab = SCREEN_TO_TAB[screen] ?? "dashboard";
  const activeIndex = TAB_ORDER.indexOf(activeTab);
  // The pill is positioned from the physical left edge with translateX, so it
  // must track the *visual* slot. In fa the row is `row-reverse`, so tab i of
  // TAB_ORDER sits in slot (n-1-i) from the left. Relying on an inherited
  // `direction` here is what put the pill on the wrong tab in the APK.
  const visualIndex = isFa ? TAB_ORDER.length - 1 - activeIndex : activeIndex;

  const [width, setWidth] = useState(0);
  const x = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!width) return;
    const center = ((visualIndex + 0.5) / TAB_ORDER.length) * width;
    Animated.spring(x, {
      toValue: center - PILL_W / 2,
      useNativeDriver: true,
      speed: 16,
      bounciness: 6,
    }).start();
  }, [visualIndex, width, x]);

  const onLayout = (e: LayoutChangeEvent) => setWidth(e.nativeEvent.layout.width);

  return (
    <View
      onLayout={onLayout}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        height: layout.bottomNavHeight,
        backgroundColor: colors.navBg,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        flexDirection: isFa ? "row-reverse" : "row",
        alignItems: "center",
        paddingBottom: 6,
      }}
    >
      <Animated.View
        pointerEvents="none"
        style={{
          position: "absolute",
          top: 8,
          left: 0,
          width: PILL_W,
          height: 44,
          borderRadius: 14,
          backgroundColor: isDark ? "rgba(157,212,184,0.10)" : "rgba(15,92,82,0.08)",
          transform: [{ translateX: x }],
        }}
      />
      {TAB_ORDER.map((tab) => {
        const meta = TAB_META[tab];
        const isActive = tab === activeTab;
        const locked = LOCKED_TABS.includes(tab);
        return (
          <Pressable
            key={tab}
            onPress={() => setTab(tab)}
            style={{ flex: 1, alignItems: "center", gap: 3 }}
          >
            <View style={{ opacity: isActive ? 1 : 0.45 }}>
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
              size={11}
              weight={isActive ? "800" : "600"}
              color={isActive ? colors.accent : colors.muted}
            >
              {t(meta.labelKey)}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}
