import React, {useEffect, useRef} from "react";
import {ActivityIndicator, Animated, Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import type {DimensionValue, ScrollViewProps, ViewProps} from "react-native";
import type {LucideIcon} from "lucide-react-native";
import {AlertCircle, RefreshCw, Sparkles} from "lucide-react-native";
import Svg, {Circle} from "react-native-svg";

import {colors, layout, radius, spacing, typography} from "../design/tokens";

type ScreenContainerProps = {children: React.ReactNode} & ScrollViewProps;

export const ScreenContainer = React.forwardRef<ScrollView, ScreenContainerProps>(function ScreenContainer(
  {children, ...scrollViewProps},
  ref,
) {
  return (
    <ScrollView
      ref={ref}
      style={styles.screen}
      contentContainerStyle={styles.screenContent}
      showsVerticalScrollIndicator={false}
      {...scrollViewProps}
    >
      {children}
      <View pointerEvents="none" style={styles.bottomNavSpacer} />
    </ScrollView>
  );
});

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

export function BrandMark({compact = false}: {compact?: boolean}) {
  return (
    <View style={styles.brand}>
      <View style={[styles.brandIcon, compact && styles.brandIconCompact]}>
        <Sparkles size={compact ? 15 : 18} color={colors.black} strokeWidth={2.8} />
      </View>
      {compact ? null : <Text style={styles.brandText}>Pharmexa</Text>}
    </View>
  );
}

export function LearningCard({
  children,
  tone = "plain",
  ...viewProps
}: {
  children: React.ReactNode;
  tone?: "plain" | "primary" | "sage" | "rose" | "amber" | "blue" | "lavender" | "mint";
} & ViewProps) {
  return (
    <View {...viewProps} style={[styles.card, toneStyles[tone], viewProps.style]}>
      {children}
    </View>
  );
}

export const GlassCard = LearningCard;

export function AnimatedEntrance({
  children,
  delay = 0,
  style,
}: {
  children: React.ReactNode;
  delay?: number;
  style?: ViewProps["style"];
}) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(14)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 280,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: 320,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, [delay, opacity, translateY]);

  return <Animated.View style={[style, {opacity, transform: [{translateY}]}]}>{children}</Animated.View>;
}

export function MetricPill({
  label,
  value,
  Icon,
}: {
  label: string;
  value: string | number;
  Icon?: LucideIcon;
}) {
  return (
    <View style={styles.metricPill}>
      {Icon ? <Icon size={14} color={colors.primary} /> : null}
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

export function ProgressRing({
  value,
  size = 116,
  strokeWidth = 10,
  label,
}: {
  value: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}) {
  const normalizedValue = Math.max(0, Math.min(100, value));
  const radiusValue = (size - strokeWidth) / 2;
  const circumference = radiusValue * 2 * Math.PI;
  const dashOffset = circumference - (normalizedValue / 100) * circumference;

  return (
    <View style={[styles.ringWrap, {width: size, height: size}]}>
      <Svg width={size} height={size} style={styles.ringSvg}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radiusValue}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
        />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radiusValue}
          fill="none"
          stroke={colors.primary}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={dashOffset}
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <View style={styles.ringCopy}>
        <Text style={styles.ringValue}>{Math.round(normalizedValue)}%</Text>
        {label ? <Text style={styles.ringLabel}>{label}</Text> : null}
      </View>
    </View>
  );
}

export function Avatar({name, size = 44}: {name?: string | null; size?: number}) {
  const initial = name?.trim().slice(0, 1).toUpperCase() || "K";
  return (
    <View style={[styles.avatar, {width: size, height: size, borderRadius: size / 2}]}>
      <Text style={[styles.avatarText, {fontSize: Math.max(14, size * 0.38)}]}>{initial}</Text>
    </View>
  );
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
      {Icon ? <Icon size={18} color={colors.black} /> : null}
      <Text style={[styles.primaryButtonText, Icon && styles.buttonTextWithIcon]}>{label}</Text>
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
      <Text style={[styles.secondaryButtonText, Icon && styles.buttonTextWithIcon]}>{label}</Text>
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

export function SectionHeader({
  title,
  action,
}: {
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionHeaderTitle}>{title}</Text>
      {action}
    </View>
  );
}

const baseShadow = {
  shadowColor: "#000000",
  shadowOpacity: 0.22,
  shadowRadius: 22,
  shadowOffset: {width: 0, height: 12},
  elevation: 5,
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screenContent: {
    width: "100%",
    maxWidth: layout.appShellMaxWidth,
    alignSelf: "center",
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xl,
  },
  bottomNavSpacer: {
    height: layout.bottomNavReservedSpace,
  },
  header: {
    minHeight: 68,
    marginBottom: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerText: {
    flex: 1,
    paddingRight: spacing.md,
  },
  eyebrow: {
    color: colors.secondary,
    fontSize: typography.small,
    fontWeight: "900",
    marginBottom: spacing.xs,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontSize: typography.title,
    fontWeight: "900",
    lineHeight: 38,
    letterSpacing: -0.6,
  },
  brand: {
    flexDirection: "row",
    alignItems: "center",
  },
  brandIcon: {
    width: 36,
    height: 36,
    borderRadius: radius.md,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.primary,
    shadowOpacity: 0.28,
    shadowRadius: 12,
    shadowOffset: {width: 0, height: 4},
  },
  brandIconCompact: {
    width: 30,
    height: 30,
  },
  brandText: {
    color: colors.ink,
    fontWeight: "900",
    fontSize: 17,
    marginLeft: spacing.sm,
  },
  card: {
    borderRadius: radius.lg,
    backgroundColor: "rgba(10,39,49,0.92)",
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
    shadowColor: colors.primary,
    shadowOpacity: 0.2,
    shadowRadius: 12,
    shadowOffset: {width: 0, height: 6},
    elevation: 4,
  },
  primaryButtonText: {
    color: colors.black,
    fontWeight: "900",
    fontSize: typography.body,
  },
  secondaryButton: {
    minHeight: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceMuted,
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
  },
  buttonTextWithIcon: {
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
    minHeight: 126,
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
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: colors.backgroundElevated,
    overflow: "hidden",
  },
  progressFill: {
    height: 8,
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
  sectionHeader: {
    minHeight: 38,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  sectionHeaderTitle: {
    color: colors.ink,
    fontSize: typography.heading,
    fontWeight: "900",
  },
  metricPill: {
    minHeight: 36,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    flexDirection: "row",
    alignItems: "center",
  },
  metricValue: {
    color: colors.ink,
    fontWeight: "900",
    marginLeft: spacing.xs,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "800",
    marginLeft: spacing.xs,
  },
  ringWrap: {
    alignItems: "center",
    justifyContent: "center",
  },
  ringSvg: {
    position: "absolute",
  },
  ringCopy: {
    alignItems: "center",
    justifyContent: "center",
  },
  ringValue: {
    color: colors.ink,
    fontSize: 23,
    fontWeight: "900",
  },
  ringLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    marginTop: 2,
  },
  avatar: {
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: {
    color: colors.primary,
    fontWeight: "900",
  },
});

const toneStyles = StyleSheet.create({
  plain: {},
  primary: {backgroundColor: colors.primarySoft, borderColor: colors.primaryMuted},
  sage: {backgroundColor: colors.sageSoft, borderColor: "rgba(101,214,164,0.25)"},
  rose: {backgroundColor: colors.roseSoft, borderColor: "rgba(255,120,146,0.25)"},
  amber: {backgroundColor: colors.amberSoft, borderColor: "rgba(244,198,106,0.25)"},
  blue: {backgroundColor: colors.blueSoft, borderColor: "rgba(85,184,255,0.25)"},
  lavender: {backgroundColor: colors.lavenderSoft, borderColor: "rgba(167,155,255,0.25)"},
  mint: {backgroundColor: colors.mintSoft, borderColor: "rgba(82,224,176,0.25)"},
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
