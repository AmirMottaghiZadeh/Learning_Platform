import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import Svg, { G, Path, Rect } from "react-native-svg";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

const methods = ["mobile", "email"] as const;
type AuthMethod = (typeof methods)[number];

function AuthMethodIcon({ method, color }: { method: AuthMethod; color: string }) {
  return (
    <View aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.icon}>
      <Svg width={20} height={20} viewBox="0 0 24 24">
        <G fill="none" stroke={color} strokeWidth={1.65} strokeLinecap="round" strokeLinejoin="round">
          {method === "mobile" ? (
            <>
              <Rect x={3.25} y={2.95} width={11.9} height={18.1} rx={3} fill={color} fillOpacity={0.24} />
              <Path d="M15.15 7.4V5.95a3 3 0 0 0-3-3h-5.9a3 3 0 0 0-3 3v12.1a3 3 0 0 0 3 3h5.9a3 3 0 0 0 3-3m-8-1.15h3.6" />
              <Path
                d="M13.5 8.1h5.6a2.25 2.25 0 0 1 2.25 2.25v2.5a2.25 2.25 0 0 1-2.25 2.25h-3.6l-3.25 1.6v-2.3a2.1 2.1 0 0 1-1-1.8v-2.25a2.25 2.25 0 0 1 2.25-2.25Z"
                fill={color}
                fillOpacity={0.24}
              />
              <Path d="M15 11.55h2.7" />
            </>
          ) : (
            <>
              <Path
                d="m3 10 7.2-6.15a2.75 2.75 0 0 1 3.6 0L21 10v7.25A2.75 2.75 0 0 1 18.25 20H5.75A2.75 2.75 0 0 1 3 17.25V10Z"
                fill={color}
                fillOpacity={0.2}
              />
              <Path d="m3.45 10.6 6.95 5.13a2.7 2.7 0 0 0 3.2 0l6.95-5.13" />
              <Path d="M9.7 8.8h4.6M10.7 11.55h2.6" />
            </>
          )}
        </G>
      </Svg>
    </View>
  );
}

export function AuthMethodSelector({ value, onChange }: { value: AuthMethod; onChange: (value: AuthMethod) => void }) {
  const { isFa, row } = useLang();
  const { colors } = useTheme();
  const labels = isFa ? { mobile: "شمارهٔ موبایل", email: "ایمیل" } : { mobile: "Mobile number", email: "Email" };

  return (
    <View
      accessibilityRole="tablist"
      testID="auth-methods"
      style={[styles.selector, { flexDirection: row }]}
    >
      {methods.map((method) => {
        const selected = value === method;
        const color = selected ? colors.accent : colors.muted;

        return (
          <Pressable
            key={method}
            accessibilityRole="tab"
            aria-selected={selected}
            accessibilityState={{ selected }}
            testID={method === "email" ? "auth-email-otp" : "auth-method-mobile"}
            onPress={() => onChange(method)}
            style={[styles.tab, { backgroundColor: selected ? colors.leitnerActiveBg : colors.softBg }]}
          >
            <AuthMethodIcon method={method} color={color} />
            <AppText size={13} weight="800" color={color}>{labels[method]}</AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  selector: { gap: 8, marginBottom: 20 },
  tab: {
    flex: 1,
    minHeight: 58,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  icon: { height: 29, alignItems: "center", justifyContent: "center" },
});
