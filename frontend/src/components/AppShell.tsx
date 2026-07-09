import React from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {
  Brain,
  CalendarCheck,
  Home,
  Layers,
  UserRound,
} from "lucide-react-native";
import type {LucideIcon} from "lucide-react-native";
import {SafeAreaView} from "react-native-safe-area-context";

import {colors, layout, radius, spacing} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";

const navItems: Array<{key: ScreenKey; label: string; Icon: LucideIcon}> = [
  {key: "dashboard", label: "Home", Icon: Home},
  {key: "quiz", label: "Learn", Icon: Brain},
  {key: "flashcards", label: "Review", Icon: Layers},
  {key: "planning", label: "Plan", Icon: CalendarCheck},
  {key: "profile", label: "Profile", Icon: UserRound},
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
  return (
    <SafeAreaView style={styles.shell}>
      <View style={styles.stage}>
        <View style={styles.appFrame}>
          <View style={styles.content}>{children}</View>
        </View>
      </View>
      <View style={styles.navWrap}>
        <View style={styles.nav}>
          {navItems.map(({key, label, Icon}) => {
            const selected = key === active;
            return (
              <Pressable
                key={key}
                accessibilityRole="button"
                accessibilityLabel={label}
                onPress={() => onNavigate(key)}
                style={[styles.navItem, selected && styles.navItemActive]}
              >
                <Icon size={20} color={selected ? colors.primary : colors.muted} strokeWidth={2.2} />
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
  },
  stage: {
    flex: 1,
    alignItems: "center",
    backgroundColor: colors.background,
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
    backgroundColor: "rgba(245,248,247,0.94)",
  },
  nav: {
    maxWidth: layout.appShellMaxWidth,
    alignSelf: "center",
    width: "100%",
    minHeight: layout.bottomNavHeight,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.xs,
    shadowColor: "#17343A",
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: {width: 0, height: 8},
    elevation: 3,
  },
  navItem: {
    width: "20%",
    minHeight: 58,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
  },
  navItemActive: {
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
  },
  navText: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  navTextActive: {
    color: colors.primary,
  },
});
