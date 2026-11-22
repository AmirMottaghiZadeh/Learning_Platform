import React from "react";
import { Pressable } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** The one theme-toggle control, used everywhere a screen offers it --
 * previously DashboardScreen, ProfileScreen, ScreenChrome and GlassToggles
 * each had their own slightly different button (a plain glyph at one size
 * here, an SVG sun/moon icon at another size there). The Home screen's
 * version (a "☀"/"☾" glyph in a translucent-white chip) is the one to match;
 * `variant="soft"` is the same button recoloured for a plain, non-colored
 * header (ScreenChrome's context) rather than a different design. */
export function ThemeToggleButton({
  variant = "chip",
  size,
}: {
  variant?: "chip" | "soft";
  size?: number;
}) {
  const { toggle, isDark, colors } = useTheme();
  const { isFa } = useLang();
  const s = size ?? 44;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={isDark ? (isFa ? "فعال‌کردن تم روشن" : "Switch to light theme") : (isFa ? "فعال‌کردن تم تاریک" : "Switch to dark theme")}
      onPress={toggle}
      hitSlop={Math.max(0, (44 - s) / 2)}
      style={({ pressed }) => ({
        opacity: pressed ? 0.8 : 1,
        width: s,
        height: s,
        borderRadius: s < 40 ? s / 2 : 12,
        alignItems: "center",
        justifyContent: "center",
        ...(variant === "chip"
          ? { backgroundColor: "rgba(255,255,255,0.16)", }
          : { backgroundColor: colors.softBg }),
      })}
    >
      <AppText size={13} color={variant === "chip" ? "#fff" : colors.accent}>
        {isDark ? "☀" : "☾"}
      </AppText>
    </Pressable>
  );
}
