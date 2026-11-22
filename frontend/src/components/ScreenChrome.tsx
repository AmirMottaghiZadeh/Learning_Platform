import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { Chevron } from "@/components/primitives/Chevron";
import { AppText } from "@/components/primitives/AppText";
import { HelpKey, HelpSheet } from "@/components/HelpSheet";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { useTourContext } from "@/tour/TourContext";
import type { TourKey } from "@/tour/tours";

/** Round soft button used across the in-app screen headers. */
export function ChromeButton({
  onPress,
  children,
  size = 44,
  variant = "soft",
  accessibilityLabel,
}: {
  onPress: () => void;
  children: React.ReactNode;
  size?: number;
  variant?: "soft" | "chip";
  accessibilityLabel?: string;
}) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      hitSlop={Math.max(0, (44 - size) / 2)}
      style={({ pressed }) => ({
        opacity: pressed ? 0.75 : 1,
        width: size,
        height: size,
        borderRadius: 12,
        backgroundColor: variant === "chip" ? "rgba(255,255,255,0.16)" : colors.softBg,
        alignItems: "center",
        justifyContent: "center",
      })}
    >
      {children}
    </Pressable>
  );
}

/** The EN/FA switch -- the only place the app's language changes, so every
 * screen that shows language-dependent content carries it in its header. */
export function LangToggleButton({ size = 44, variant = "soft" }: { size?: number; variant?: "soft" | "chip" } = {}) {
  const { colors } = useTheme();
  const { t, toggle } = useLang();
  return (
    <Pressable
      onPress={toggle}
      accessibilityRole="button"
      accessibilityLabel={t("langSwitch") === "EN" ? "Switch to English" : "تغییر زبان به فارسی"}
      hitSlop={Math.max(0, (44 - size) / 2)}
      style={{
        minWidth: size,
        minHeight: size,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: variant === "chip" ? "rgba(255,255,255,0.16)" : colors.softBg,
        borderRadius: 12,
        paddingHorizontal: 10,
        paddingVertical: 6,
      }}
    >
      <AppText weight="800" size={12} color={variant === "chip" ? colors.flipFrontInk : colors.accent}>
        {t("langSwitch")}
      </AppText>
    </Pressable>
  );
}

/** Title row + theme / language toggles, matching the design's screen headers. */
/** The "?" that replays a section's guided tour. */
export function TourButton({ tour, size = 44 }: { tour: TourKey; size?: number }) {
  const { colors } = useTheme();
  const tours = useTourContext();
  const { isFa } = useLang();
  return (
    <ChromeButton onPress={() => tours?.start(tour)} size={size} accessibilityLabel={isFa ? "راهنمای صفحه" : "Screen tour"}>
      <AppText weight="800" size={13} color={colors.accent}>
        ?
      </AppText>
    </ChromeButton>
  );
}

export function ScreenChrome({
  title,
  onBack,
  help,
  tour,
  actions,
}: {
  title: string;
  onBack?: () => void;
  /** the old text help sheet, for a screen without a tour */
  help?: HelpKey;
  /** the section's guided tour: "?" replays it */
  tour?: TourKey;
  /** extra buttons at the start of the header's button group */
  actions?: React.ReactNode;
}) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const [helpOpen, setHelpOpen] = useState(false);

  return (
    <View
      style={{
        flexDirection: row,
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 14,
      }}
    >
      <View style={{ flexDirection: row, alignItems: "center", gap: 10, flex: 1 }}>
        {onBack ? (
          <ChromeButton onPress={onBack} accessibilityLabel={isFa ? "بازگشت" : "Back"}>
            <Chevron back color={colors.ink} />
          </ChromeButton>
        ) : null}
        <AppText accessibilityRole="header" aria-level={1} weight="700" size={17} style={{ flex: 1 }}>
          {title}
        </AppText>
      </View>
      <View style={{ flexDirection: row, gap: 8, alignItems: "center" }}>
        {actions}
        {tour ? <TourButton tour={tour} /> : help ? (
          <ChromeButton onPress={() => setHelpOpen(true)} accessibilityLabel={isFa ? "راهنمای صفحه" : "Screen help"}>
            <AppText weight="800" size={13} color={colors.accent}>
              ?
            </AppText>
          </ChromeButton>
        ) : null}
        <ThemeToggleButton variant="soft" />
        <LangToggleButton />
      </View>
      {help && !tour ? (
        <HelpSheet helpKey={helpOpen ? help : null} onClose={() => setHelpOpen(false)} />
      ) : null}
    </View>
  );
}
