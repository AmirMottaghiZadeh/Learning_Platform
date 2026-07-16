import React, {useEffect, useRef} from "react";
import {ActivityIndicator, Animated, Image, ImageSourcePropType, Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import type {ImageStyle, ScrollViewProps, ViewProps} from "react-native";
import type {LucideIcon} from "lucide-react-native";
import {AlertCircle, RefreshCw} from "lucide-react-native";
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
    <Image
      source={require("../../assets/pharmexa-wordmark.png")}
      resizeMode="contain"
      style={[styles.brandWordmark, compact && styles.brandWordmarkCompact]}
    />
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

export function GlassCard({children, ...viewProps}: {children: React.ReactNode} & ViewProps) {
  return <View {...viewProps} style={[styles.glassCard, viewProps.style]}>{children}</View>;
}

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

export function FloatingIllustration({
  source,
  size = 120,
  style,
}: {
  source: ImageSourcePropType;
  size?: number;
  style?: ImageStyle;
}) {
  const translateY = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(translateY, {toValue: -8, duration: 2200, useNativeDriver: true}),
        Animated.timing(translateY, {toValue: 0, duration: 2200, useNativeDriver: true}),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [translateY]);

  return (
    <Animated.Image
      source={source}
      resizeMode="contain"
      style={[{width: size, height: size, transform: [{translateY}]}, style]}
    />
  );
}

const PARTICLES = [
  {left: "12%", top: "14%", color: colors.primary, offsetX: -30, offsetY: -38, size: 7},
  {left: "28%", top: "8%", color: colors.secondary, offsetX: 10, offsetY: -46, size: 5},
  {left: "47%", top: "18%", color: colors.amber, offsetX: 22, offsetY: -32, size: 8},
  {left: "66%", top: "9%", color: colors.lavender, offsetX: 30, offsetY: -44, size: 6},
  {left: "82%", top: "19%", color: colors.mint, offsetX: 40, offsetY: -26, size: 5},
] as const;

export function CelebrationParticles({active}: {active: boolean}) {
  const progress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    progress.stopAnimation();
    progress.setValue(0);
    if (!active) return;

    Animated.timing(progress, {
      toValue: 1,
      duration: 850,
      useNativeDriver: true,
    }).start();
  }, [active, progress]);

  if (!active) return null;

  return (
    <View pointerEvents="none" style={styles.particleLayer}>
      {PARTICLES.map((particle, index) => {
        const translateX = progress.interpolate({inputRange: [0, 1], outputRange: [0, particle.offsetX]});
        const translateY = progress.interpolate({inputRange: [0, 1], outputRange: [0, particle.offsetY]});
        const opacity = progress.interpolate({inputRange: [0, 0.15, 1], outputRange: [0, 1, 0]});
        const scale = progress.interpolate({inputRange: [0, 0.35, 1], outputRange: [0.4, 1, 0.6]});
        return (
          <Animated.View
            key={index}
            style={[
              styles.particle,
              {
                left: particle.left,
                top: particle.top,
                width: particle.size,
                height: particle.size,
                borderRadius: particle.size / 2,
                backgroundColor: particle.color,
                opacity,
                transform: [{translateX}, {translateY}, {scale}],
              },
            ]}
          />
        );
      })}
    </View>
  );
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
  const progress = useRef(new Animated.Value(0)).current;
  const normalizedValue = Math.max(0, Math.min(100, value));

  useEffect(() => {
    Animated.timing(progress, {
      toValue: normalizedValue,
      duration: 760,
      useNativeDriver: false,
    }).start();
  }, [normalizedValue, progress]);

  const width = progress.interpolate({
    inputRange: [0, 100],
    outputRange: ["0%", "100%"],
    extrapolate: "clamp",
  });

  return (
    <View style={styles.progressTrack}>
      <Animated.View style={[styles.progressFill, {width}]} />
    </View>
  );
}

export function LoadingState({label = "در حال بارگذاری"}: {label?: string}) {
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
      {onRetry ? <SecondaryButton label="تلاش دوباره" Icon={RefreshCw} onPress={onRetry} /> : null}
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

export function SkeletonCard({height = 120, style}: {height?: number; style?: ViewProps["style"]}) {
  return <View style={[styles.skeletonCard, {height}, style]} />;
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
    backgroundColor: "transparent",
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
  },
  title: {
    color: colors.ink,
    fontSize: typography.title,
    fontWeight: "900",
    lineHeight: 38,
    letterSpacing: -0.6,
  },
  brandWordmark: {
    width: 142,
    height: 34,
  },
  brandWordmarkCompact: {
    width: 112,
    height: 27,
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
  glassCard: {
    borderRadius: radius.lg,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.borderStrong,
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
    transform: [{scale: 0.97}],
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
  particleLayer: {
    ...StyleSheet.absoluteFill,
    overflow: "hidden",
  },
  particle: {
    position: "absolute",
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
  skeletonCard: {
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
    opacity: 0.7,
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
