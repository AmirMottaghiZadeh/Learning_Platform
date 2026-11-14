import React, { useEffect, useRef, useState } from "react";
import { AccessibilityInfo, Animated, Easing, Platform, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

function useLoadingPulse() {
  const pulse = useRef(new Animated.Value(0)).current;
  const [reducedMotion, setReducedMotion] = useState(true);
  useEffect(() => {
    let mounted = true;
    let preferenceChanged = false;
    const subscription = AccessibilityInfo.addEventListener("reduceMotionChanged", (reduced) => {
      preferenceChanged = true;
      setReducedMotion(reduced);
    });
    void AccessibilityInfo.isReduceMotionEnabled().then((reduced) => {
      if (mounted && !preferenceChanged) setReducedMotion(reduced);
    }).catch(() => { /* Keep the static indicator if the preference is unavailable. */ });
    return () => { mounted = false; subscription.remove(); };
  }, []);
  useEffect(() => {
    if (reducedMotion) { pulse.setValue(0.5); return; }
    pulse.setValue(0);
    const animation = Animated.loop(Animated.timing(pulse, {
      toValue: 1, duration: 1800, easing: Easing.linear, useNativeDriver: Platform.OS !== "web",
      isInteraction: false,
    }));
    animation.start();
    return () => animation.stop();
  }, [pulse, reducedMotion]);
  return { pulse, reducedMotion };
}

/** Reserve the final answer's place even while source results arrive below it. */
export function ReferenceAnswerSkeleton() {
  const { colors } = useTheme();
  const { isFa } = useLang();
  const { pulse, reducedMotion } = useLoadingPulse();
  const label = isFa ? "پاسخ فارسی در حال آماده‌سازی است…" : "Preparing your answer…";
  return <View testID="reference-answer-skeleton" accessible accessibilityRole="progressbar"
    accessibilityLabel={label} accessibilityState={{ busy: true }} aria-busy style={{ gap: 16 }}>
    <Animated.View importantForAccessibility="no-hide-descendants" aria-hidden
      style={{ gap: 12, paddingVertical: 6, alignItems: isFa ? "flex-end" : "flex-start", opacity: reducedMotion ? 0.5
        : pulse.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0.35, 0.7, 0.35] }) }}>
      {(["100%", "94%", "100%", "64%"] as const).map((width, index) => <View key={index}
        style={{ width, height: 9, borderRadius: 5, backgroundColor: colors.trackBg }} />)}
    </Animated.View>
    <AppText size={12} muted>{label}</AppText>
  </View>;
}

/** Source results load independently from the final Persian answer above them. */
export function ReferenceSearchLoading({ hasResults = false }: { hasResults?: boolean }) {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const { pulse, reducedMotion } = useLoadingPulse();
  const label = isFa ? hasResults ? "در حال بررسی منابع بیشتر…" : "در حال یافتن بخش‌های مرتبط…"
    : hasResults ? "Checking more sources…" : "Finding relevant passages…";
  return <View testID="reference-streaming-loading" accessible accessibilityRole="progressbar"
    accessibilityLabel={label} accessibilityState={{ busy: true }} aria-busy
    style={{ paddingVertical: 10 }}>
    <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 4 }}>
        {[0, 1, 2].map((dot) => <Animated.View key={dot} style={{
          width: 6, height: 6, borderRadius: 3, backgroundColor: colors.accent,
          opacity: reducedMotion ? 0.7 : pulse.interpolate({
            inputRange: [0, 0.2 + dot * 0.15, 0.5 + dot * 0.15, 1],
            outputRange: [0.25, 1, 0.25, 0.25],
          }),
        }} />)}
      </View>
      <AppText size={13} color={colors.accent}>{label}</AppText>
    </View>
  </View>;
}
