import React from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {
  Brain,
  Home,
  Layers,
  Trophy,
  UserRound,
} from "lucide-react-native";
import type {LucideIcon} from "lucide-react-native";
import {SafeAreaView} from "react-native-safe-area-context";

import {colors, layout, radius, spacing} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";

const navItems: Array<{key: ScreenKey; label: string; Icon: LucideIcon}> = [
  {key: "dashboard", label: "خانه", Icon: Home},
  {key: "quiz", label: "آزمون", Icon: Brain},
  {key: "flashcards", label: "فلش‌کارت", Icon: Layers},
  {key: "league", label: "لیگ", Icon: Trophy},
  {key: "profile", label: "پروفایل", Icon: UserRound},
];

export function AppShell({
  active,
  onNavigate,
  children,
}: {
  active: ScreenKey;
  onNavigate: (screen: ScreenKey) => void;
  children: React.ReactNode;
}) {
  const activeNavKey: ScreenKey =
    active === "planning" || active === "mistakes" || active === "statistics" ? "dashboard" : active;

  return (
    <SafeAreaView style={styles.shell}>
      <View style={styles.stage}>
        <View pointerEvents="none" style={styles.glowTop} />
        <View pointerEvents="none" style={styles.glowBottom} />
        <View style={styles.appFrame}>
          <View style={styles.content}>{children}</View>
        </View>
      </View>
      <View style={styles.navWrap}>
        <View style={styles.nav}>
          {navItems.map(({key, label, Icon}) => {
            const selected = key === activeNavKey;
            return (
              <Pressable
                key={key}
                accessibilityRole="button"
                accessibilityLabel={label}
                onPress={() => onNavigate(key)}
                style={[styles.navItem, selected && styles.navItemActive]}
              >
                <Icon size={20} color={selected ? colors.black : colors.muted} strokeWidth={2.2} />
                <Text style={[styles.navText, selected && styles.navTextActive]} numberOfLines={1}>
                  {label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  shell: {
    flex: 1,
    backgroundColor: colors.background,
    overflow: "hidden",
  },
  stage: {
    flex: 1,
    alignItems: "center",
    backgroundColor: colors.background,
  },
  glowTop: {
    position: "absolute",
    top: -190,
    right: -130,
    width: 390,
    height: 390,
    borderRadius: radius.pill,
    backgroundColor: "rgba(32,242,138,0.07)",
  },
  glowBottom: {
    position: "absolute",
    bottom: -210,
    left: -150,
    width: 420,
    height: 420,
    borderRadius: radius.pill,
    backgroundColor: "rgba(34,215,197,0.05)",
  },
  appFrame: {
    width: "100%",
    maxWidth: layout.appShellMaxWidth,
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
  },
  navWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    backgroundColor: "transparent",
  },
  nav: {
    maxWidth: layout.appShellMaxWidth,
    alignSelf: "center",
    width: "100%",
    minHeight: layout.bottomNavHeight,
    borderRadius: radius.pill,
    backgroundColor: "rgba(8,38,48,0.96)",
    borderWidth: 1,
    borderColor: colors.borderStrong,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.sm,
    shadowColor: "#000000",
    shadowOpacity: 0.35,
    shadowRadius: 24,
    shadowOffset: {width: 0, height: 12},
    elevation: 12,
  },
  navItem: {
    width: "20%",
    minHeight: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.pill,
  },
  navItemActive: {
    backgroundColor: colors.primary,
  },
  navText: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  navTextActive: {
    color: colors.black,
  },
});
