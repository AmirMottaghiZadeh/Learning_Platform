import React from "react";
import {StyleSheet, Text} from "react-native";
import {LogOut, Server, UserRound} from "lucide-react-native";

import {API_BASE_URL} from "../api/client";
import {LearningCard, PrimaryButton, ScreenContainer, ScreenHeader} from "../components/ui";
import {colors, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";

export function ProfileScreen() {
  const {user, signOut} = useAuth();
  return (
    <ScreenContainer>
      <ScreenHeader eyebrow="Account" title="Profile" />
      <LearningCard tone="blue">
        <UserRound size={28} color={colors.blue} />
        <Text style={styles.name}>{user?.username}</Text>
        <Text style={styles.meta}>{user?.email || "No email"}</Text>
      </LearningCard>
      <LearningCard>
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
});
