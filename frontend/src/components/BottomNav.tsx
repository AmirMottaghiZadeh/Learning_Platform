import React from "react";
import { Pressable, View } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";
import { LOCKED_TABS, TAB_ORDER, TabKey } from "@/navigation/types";
import { AppText } from "./primitives/AppText";
import { IconImage, IconName } from "./primitives/IconImage";

const TAB_META: Record<TabKey, { icon: IconName; labelKey: "navHome" | "lessonsLabel" | "cardsLabel" | "quizLabel" | "profileLabel" }> = {
  dashboard: { icon: "phoneHealth", labelKey: "navHome" },
  lessons: { icon: "openBook", labelKey: "lessonsLabel" },
  flashcards: { icon: "mobileBlister", labelKey: "cardsLabel" },
  quiz: { icon: "checklist", labelKey: "quizLabel" },
  profile: { icon: "team", labelKey: "profileLabel" },
};

export function BottomNav() {
  const { colors } = useTheme();
  const { t } = useLang();
  const active = useNav((s) => s.screen);
  const setTab = useNav((s) => s.setTab);

  return (
    <View
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        height: layout.bottomNavHeight,
        backgroundColor: colors.navBg,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-around",
        paddingBottom: 6,
      }}
    >
      {TAB_ORDER.map((tab) => {
        const meta = TAB_META[tab];
        const isActive = active === tab;
        const locked = LOCKED_TABS.includes(tab);
        return (
          <Pressable
            key={tab}
            onPress={() => setTab(tab)}
            style={{ alignItems: "center", gap: 3, width: 56 }}
          >
            <View style={{ opacity: isActive ? 1 : 0.5 }}>
              <IconImage name={meta.icon} size={24} />
              {locked ? (
                <View
                  style={{
                    position: "absolute",
                    top: -4,
                    right: -6,
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: colors.cautLabel,
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
