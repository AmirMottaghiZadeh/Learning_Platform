import React from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { LRI, PDI } from "@/utils/bidi";
import { UnitSystem } from "@/utils/calculatorLabels";

/** The calculator's SI/US switch, for choices written in both units: each
 * side is named by its own units (µmol/L, °C | mg/dL, °F), so the learner
 * picks what their lab report uses. Numeric answers keep their own unit
 * switch beside the field. */
export function UnitSystemSwitch({
  units,
  value,
  onChange,
}: {
  units: Record<UnitSystem, string[]>;
  value: UnitSystem;
  onChange: (system: UnitSystem) => void;
}) {
  const { colors } = useTheme();
  const { t, isFa, row } = useLang();
  const sides: UnitSystem[] = ["si", "us"];

  return (
    <View style={{ flexDirection: row, alignItems: "center", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
      <AppText weight="800" size={12.5} muted style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
        {t("calcUnitSystem")}
      </AppText>
      <View
        style={{
          flexDirection: "row",
          borderRadius: 999,
          borderWidth: 1,
          borderColor: colors.border,
          backgroundColor: colors.softBg,
          overflow: "hidden",
        }}
      >
        {sides.map((side) => {
          const selected = side === value;
          const names = units[side].join(", ");
          return (
            <Pressable
              key={side}
              onPress={() => onChange(side)}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              style={{ paddingHorizontal: 14, paddingVertical: 7, backgroundColor: selected ? colors.accent : "transparent" }}
            >
              <AppText weight="800" size={12} color={selected ? colors.onAccent : colors.muted} style={{ writingDirection: "ltr", textAlign: "left" }}>
                {/* Isolated left-to-right, or the page's right-to-left layout
                    moves the leading «°» of «°C» to the far end. */}
                {`${LRI}${names || side.toUpperCase()}${PDI}`}
              </AppText>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}
