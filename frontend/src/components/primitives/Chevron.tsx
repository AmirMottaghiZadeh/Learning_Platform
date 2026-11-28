import React from "react";
import Svg, { Path } from "react-native-svg";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export function Chevron({ back = false, color }: { back?: boolean; color?: string }) {
  const { isFa } = useLang();
  const { colors } = useTheme();
  const pointsRight = back === isFa;

  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" accessibilityElementsHidden aria-hidden>
      <Path
        d={pointsRight ? "m9 6 6 6-6 6" : "m15 6-6 6 6 6"}
        stroke={color ?? colors.muted}
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}
