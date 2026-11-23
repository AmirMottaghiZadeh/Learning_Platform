import React from "react";

import { ChromeButton } from "@/components/ChromeButton";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export function ThemeToggleButton({
  variant = "chip",
  size,
}: {
  variant?: "chip" | "soft";
  size?: number;
}) {
  const { toggle, isDark, colors } = useTheme();
  const { isFa } = useLang();

  return (
    <ChromeButton
      accessibilityLabel={isDark ? (isFa ? "فعال‌کردن تم روشن" : "Switch to light theme") : (isFa ? "فعال‌کردن تم تاریک" : "Switch to dark theme")}
      onPress={toggle}
      size={size}
      variant={variant === "chip" ? "chip" : "control"}
    >
      <AppText size={13} color={variant === "chip" ? colors.flipFrontInk : colors.accent}>
        {isDark ? "☀" : "☾"}
      </AppText>
    </ChromeButton>
  );
}
