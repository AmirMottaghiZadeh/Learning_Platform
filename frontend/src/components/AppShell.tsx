import React, {useEffect} from "react";
import {
  Image,
  LayoutAnimation,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  UIManager,
  View,
} from "react-native";
import type {ImageSourcePropType} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";

import {FloatingIllustration} from "./ui";
import {colors, featureAccents, layout, radius, spacing} from "../design/tokens";
import type {ScreenKey} from "../navigation/types";

const navItems: Array<{key: ScreenKey; label: string; source: ImageSourcePropType; accent: string}> = [
  {
    key: "dashboard",
    label: "خانه",
    source: require("../../assets/illustrations/hero-target.png"),
    accent: colors.primary,
  },
  {
    key: "quiz",
    label: "آزمون",
    source: require("../../assets/illustrations/quiz-brain.png"),
    accent: featureAccents.quiz.color,
  },
  {
    key: "flashcards",
    label: "فلش‌کارت",
    source: require("../../assets/illustrations/flashcards-stack.png"),
    accent: featureAccents.flashcards.color,
  },
  {
    key: "league",
    label: "لیگ",
    source: require("../../assets/illustrations/league-trophy.png"),
    accent: featureAccents.leaderboard.color,
  },
  {
    key: "profile",
    label: "پروفایل",
    source: require("../../assets/illustrations/profile-insights.png"),
    accent: featureAccents.profile.color,
  },
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
  useEffect(() => {
    if (Platform.OS === "android" && UIManager.setLayoutAnimationEnabledExperimental) {
      UIManager.setLayoutAnimationEnabledExperimental(true);
    }
  }, []);

  const activeNavKey: ScreenKey =
    active === "planning" || active === "mistakes" || active === "statistics" ? "dashboard" : active;

  return (
    <SafeAreaView style={styles.shell}>
      <View pointerEvents="none" style={styles.mesh}>
        <Image source={require("../../assets/mesh-background-v3.jpg")} resizeMode="cover" style={styles.meshImage} />
      </View>
      <View pointerEvents="none" style={styles.meshVeil} />
      <View style={styles.stage}>
        <View style={styles.appFrame}>
          <View style={styles.content}>{children}</View>
        </View>
      </View>

      {active !== "dashboard" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="ماموریت امروز"
          onPress={() => onNavigate("dashboard")}
          style={({pressed}) => [styles.floatingMission, pressed && styles.floatingMissionPressed]}
        >
          <FloatingIllustration source={require("../../assets/illustrations/hero-target.png")} size={42} />
          <Text style={styles.floatingMissionText}>ماموریت امروز</Text>
        </Pressable>
      ) : null}

      <View style={styles.navWrap}>
        <View style={styles.nav}>
          {navItems.map(({key, label, source, accent}) => {
            const selected = key === activeNavKey;
            return (
              <Pressable
                key={key}
                accessibilityRole="button"
                accessibilityLabel={label}
                onPress={() => {
                  LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
                  onNavigate(key);
                }}
                style={[styles.navItem, selected && styles.navItemActive]}
              >
                <View style={[styles.navIconWrap, selected && {backgroundColor: `${accent}2A`}]}>
                  <Image source={source} style={[styles.navIcon, !selected && styles.navIconMuted]} />
                </View>
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
    backgroundColor: "transparent",
    zIndex: 2,
  },
  mesh: {
    ...StyleSheet.absoluteFill,
    opacity: 0.72,
    zIndex: 0,
  },
  meshImage: {
    width: "100%",
    height: "100%",
  },
  meshVeil: {
    ...StyleSheet.absoluteFill,
    backgroundColor: "rgba(3,24,32,0.56)",
    zIndex: 1,
  },
  appFrame: {
    width: "100%",
    maxWidth: layout.appShellMaxWidth,
    flex: 1,
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
    zIndex: 4,
  },
  nav: {
    maxWidth: layout.appShellMaxWidth,
    alignSelf: "center",
    width: "100%",
    minHeight: layout.bottomNavHeight,
    borderRadius: radius.pill,
    backgroundColor: colors.glassStrong,
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
    backgroundColor: "rgba(255,255,255,0.08)",
  },
  navIconWrap: {
    width: 28,
    height: 28,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  navIcon: {
    width: 25,
    height: 25,
  },
  navIconMuted: {
    opacity: 0.55,
  },
  navText: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: spacing.xs,
  },
  navTextActive: {
    color: colors.ink,
  },
  floatingMission: {
    position: "absolute",
    right: spacing.lg,
    bottom: layout.bottomNavHeight + spacing.xxl,
    minHeight: 54,
    borderRadius: radius.pill,
    backgroundColor: colors.glassStrong,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    paddingRight: spacing.md,
    paddingLeft: spacing.xs,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: "#000000",
    shadowOpacity: 0.28,
    shadowRadius: 20,
    shadowOffset: {width: 0, height: 8},
    elevation: 8,
    zIndex: 5,
  },
  floatingMissionPressed: {
    transform: [{scale: 0.97}],
  },
  floatingMissionText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
});
