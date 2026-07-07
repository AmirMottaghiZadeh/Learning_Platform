import React from "react";
import {ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import type {DimensionValue} from "react-native";
import type {LucideIcon} from "lucide-react-native";
import {AlertCircle, RefreshCw} from "lucide-react-native";

import {colors, layout, radius, spacing, typography} from "../design/tokens";

export function ScreenContainer({children}: {children: React.ReactNode}) {
  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.screenContent}
      showsVerticalScrollIndicator={false}
    >
      {children}
      <View pointerEvents="none" style={styles.bottomNavSpacer} />
    </ScrollView>
  );
}

export function ScreenHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow?: string;
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <View style={styles.header}>
      <View style={styles.headerText}>
        {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
        <Text style={styles.title}>{title}</Text>
      </View>
      {action}
    </View>
  );
}

export function LearningCard({
  children,
  tone = "plain",
}: {
  children: React.ReactNode;
  tone?: "plain" | "primary" | "sage" | "rose" | "amber" | "blue" | "lavender" | "mint";
}) {
  return <View style={[styles.card, toneStyles[tone]]}>{children}</View>;
}

export function IconBadge({Icon, tone = "primary"}: {Icon: LucideIcon; tone?: keyof typeof badgeStyles}) {
  return (
    <View style={[styles.iconBadge, badgeStyles[tone]]}>
      <Icon size={18} color={colors.ink} strokeWidth={2.1} />
    </View>
  );
}

export function PrimaryButton({
  label,
  Icon,
  onPress,
  disabled,
}: {
  label: string;
  Icon?: LucideIcon;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({pressed}) => [
        styles.primaryButton,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      {Icon ? <Icon size={18} color="#FFFFFF" /> : null}
      <Text style={styles.primaryButtonText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({
  label,
  Icon,
  onPress,
  disabled,
}: {
  label: string;
  Icon?: LucideIcon;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({pressed}) => [
        styles.secondaryButton,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      {Icon ? <Icon size={18} color={colors.ink} /> : null}
      <Text style={styles.secondaryButtonText}>{label}</Text>
    </Pressable>
  );
}

export function StatTile({
  label,
  value,
  Icon,
  tone = "primary",
}: {
  label: string;
  value: string | number;
  Icon: LucideIcon;
  tone?: keyof typeof badgeStyles;
}) {
  return (
    <View style={styles.statTile}>
      <IconBadge Icon={Icon} tone={tone} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export function ProgressBar({value}: {value: number}) {
  const width = `${Math.max(0, Math.min(100, value))}%` as DimensionValue;
  return (
    <View style={styles.progressTrack}>
      <View style={[styles.progressFill, {width}]} />
    </View>
  );
}

export function LoadingState({label = "Loading"}: {label?: string}) {
  return (
    <View style={styles.stateBox}>
      <ActivityIndicator color={colors.primary} />
      <Text style={styles.stateText}>{label}</Text>
    </View>
  );
}

export function EmptyState({title}: {title: string}) {
  return (
    <View style={styles.stateBox}>
      <Text style={styles.emptyText}>{title}</Text>
    </View>
  );
}

export function ErrorState({message, onRetry}: {message: string; onRetry?: () => void}) {
  return (
    <View style={styles.stateBox}>
      <AlertCircle size={24} color={colors.danger} />
      <Text style={styles.stateText}>{message}</Text>
      {onRetry ? <SecondaryButton label="Retry" Icon={RefreshCw} onPress={onRetry} /> : null}
    </View>
  );
}

export function SectionTitle({children}: {children: React.ReactNode}) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

const baseShadow = {
  shadowColor: "#17343A",
  shadowOpacity: 0.06,
  shadowRadius: 20,
  shadowOffset: {width: 0, height: 10},
  elevation: 2,
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screenContent: {
    width: "100%",
    maxWidth: 760,
    alignSelf: "center",
    paddingHorizontal: spacing.md,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
  },
  bottomNavSpacer: {
    height: layout.bottomNavReservedSpace,
  },
  header: {
    minHeight: 72,
    marginBottom: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerText: {
    flex: 1,
    paddingRight: spacing.md,
  },
  eyebrow: {
    color: colors.primary,
    fontSize: typography.small,
    fontWeight: "900",
    marginBottom: spacing.xs,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontSize: typography.title,
    fontWeight: "900",
    lineHeight: 36,
  },
  card: {
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...baseShadow,
  },
  primaryButton: {
    minHeight: 48,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.primary,
  },
  primaryButtonText: {
    color: "#FFFFFF",
    fontWeight: "800",
    fontSize: typography.body,
    marginLeft: spacing.sm,
  },
  secondaryButton: {
    minHeight: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  secondaryButtonText: {
    color: colors.ink,
    fontWeight: "800",
    fontSize: typography.body,
    marginLeft: spacing.sm,
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    transform: [{scale: 0.99}],
  },
  iconBadge: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  statTile: {
    width: "48%",
    minHeight: 132,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  statValue: {
    color: colors.ink,
    fontSize: 23,
    fontWeight: "900",
  },
  statLabel: {
    color: colors.muted,
    fontSize: typography.small,
    fontWeight: "700",
    marginTop: spacing.xs,
  },
  progressTrack: {
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: colors.backgroundElevated,
    overflow: "hidden",
  },
  progressFill: {
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  stateBox: {
    minHeight: 150,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  stateText: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "700",
    textAlign: "center",
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  emptyText: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "800",
    textAlign: "center",
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
});

const toneStyles = StyleSheet.create({
  plain: {},
  primary: {backgroundColor: colors.primarySoft, borderColor: colors.primaryMuted},
  sage: {backgroundColor: colors.sageSoft, borderColor: "#BFD6CB"},
  rose: {backgroundColor: colors.roseSoft, borderColor: "#E2C0C7"},
  amber: {backgroundColor: colors.amberSoft, borderColor: "#E2CCA7"},
  blue: {backgroundColor: colors.blueSoft, borderColor: "#BED4E5"},
  lavender: {backgroundColor: colors.lavenderSoft, borderColor: "#CEC7DC"},
  mint: {backgroundColor: colors.mintSoft, borderColor: "#BBDACF"},
});

const badgeStyles = StyleSheet.create({
  primary: {backgroundColor: colors.primarySoft},
  sage: {backgroundColor: colors.sageSoft},
  rose: {backgroundColor: colors.roseSoft},
  amber: {backgroundColor: colors.amberSoft},
  blue: {backgroundColor: colors.blueSoft},
  lavender: {backgroundColor: colors.lavenderSoft},
  mint: {backgroundColor: colors.mintSoft},
});
