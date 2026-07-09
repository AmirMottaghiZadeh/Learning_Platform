import React from "react";
import {StyleSheet, Text, View} from "react-native";
import {BookOpenCheck, Headphones, LogOut, RotateCcw, Server, ShieldCheck, Star, UserRound} from "lucide-react-native";

import {API_BASE_URL} from "../api/client";
import {LearningCard, PrimaryButton, ScreenContainer, ScreenHeader} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";
import {useOnboarding} from "../store/onboarding";

export function ProfileScreen() {
  const {user, signOut} = useAuth();
  const {resetOnboarding} = useOnboarding();
  return (
    <ScreenContainer>
      <ScreenHeader eyebrow="Account" title="Profile" />
      <LearningCard tone="mint">
        <UserRound size={28} color={colors.primary} />
        <Text style={styles.name}>{user?.username}</Text>
        <Text style={styles.meta}>{user?.email || "No email"}</Text>
      </LearningCard>
      <LearningCard tone="amber">
        <View style={styles.row}>
          <ShieldCheck size={24} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.label}>Subscription</Text>
            <Text style={styles.meta}>Free learning path · Upgrade CTA ready</Text>
          </View>
        </View>
      </LearningCard>
      <LearningCard tone="lavender">
        <View style={styles.row}>
          <Headphones size={24} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.label}>Personal guide</Text>
            <Text style={styles.meta}>Need a study plan? Contact support or request guidance.</Text>
          </View>
        </View>
      </LearningCard>
      <LearningCard tone="sage">
        <View style={styles.row}>
          <BookOpenCheck size={24} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.label}>Learning cycle</Text>
            <Text style={styles.meta}>Learn → quiz → mistakes → flashcards → statistics → return tomorrow.</Text>
          </View>
        </View>
      </LearningCard>
      <PrimaryButton label="Upgrade to full access" Icon={Star} onPress={() => undefined} />
      <View style={styles.spacer} />
      <PrimaryButton label="Replay onboarding" Icon={RotateCcw} onPress={resetOnboarding} />
      <LearningCard tone="blue">
        <Server size={24} color={colors.primary} />
        <Text style={styles.label}>API</Text>
        <Text style={styles.meta}>{API_BASE_URL}</Text>
      </LearningCard>
      <PrimaryButton label="Logout" Icon={LogOut} onPress={signOut} />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  name: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  label: {
    color: colors.ink,
    fontWeight: "900",
    marginTop: spacing.md,
  },
  meta: {
    color: colors.muted,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  rowText: {
    flex: 1,
    marginLeft: spacing.md,
  },
  spacer: {
    height: spacing.sm,
  },
});
