import React, { useState } from "react";
import { View } from "react-native";

import { ChromeButton } from "@/components/ChromeButton";
import { Chevron } from "@/components/primitives/Chevron";
import { AppText } from "@/components/primitives/AppText";
import { HelpKey, HelpSheet } from "@/components/HelpSheet";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { useTourContext } from "@/tour/TourContext";
import type { TourKey } from "@/tour/tours";

export { ChromeButton };

/** The EN/FA switch -- the only place the app's language changes, so every
 * screen that shows language-dependent content carries it in its header. */
export function LangToggleButton({ size = 44, variant = "soft" }: { size?: number; variant?: "soft" | "chip" } = {}) {
  const { colors } = useTheme();
  const { t, toggle } = useLang();
  return (
    <ChromeButton
      onPress={toggle}
      size={size}
      variant={variant === "chip" ? "chip" : "control"}
      accessibilityLabel={t("langSwitch") === "EN" ? "Switch to English" : "تغییر زبان به فارسی"}
    >
      <AppText weight="800" size={12} color={variant === "chip" ? colors.flipFrontInk : colors.accent}>
        {t("langSwitch")}
      </AppText>
    </ChromeButton>
  );
}

/** Title row + theme / language toggles, matching the design's screen headers. */
/** The "?" that replays a section's guided tour. */
export function TourButton({ tour, size = 44 }: { tour: TourKey; size?: number }) {
  const { colors } = useTheme();
  const tours = useTourContext();
  const { isFa } = useLang();
  return (
    <ChromeButton variant="control" onPress={() => tours?.start(tour)} size={size} accessibilityLabel={isFa ? "راهنمای صفحه" : "Screen tour"}>
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
          <ChromeButton variant="control" onPress={() => setHelpOpen(true)} accessibilityLabel={isFa ? "راهنمای صفحه" : "Screen help"}>
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
