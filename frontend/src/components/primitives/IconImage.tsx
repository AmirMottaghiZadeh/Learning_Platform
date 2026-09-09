import React from "react";
import { Image, ImageStyle, StyleProp } from "react-native";

// Static registry — Metro needs literal require() paths.
export const ICONS = {
  mortar: require("../../../assets/icons/mortar.png"),
  phoneHealth: require("../../../assets/icons/phone-health.png"),
  openBook: require("../../../assets/icons/open-book.png"),
  mobileBlister: require("../../../assets/icons/mobile-blister.png"),
  checklist: require("../../../assets/icons/checklist.png"),
  team: require("../../../assets/icons/team.png"),
  docSearch: require("../../../assets/icons/doc-search.png"),
  chartGrowth: require("../../../assets/icons/chart-growth.png"),
  calendarPill: require("../../../assets/icons/calendar-pill.png"),
  pillWarning: require("../../../assets/icons/pill-warning.png"),
  bulbBrain: require("../../../assets/icons/bulb-brain.png"),
  graduation: require("../../../assets/icons/graduation.png"),
} as const;

export type IconName = keyof typeof ICONS;

export function IconImage({
  name,
  size = 24,
  style,
}: {
  name: IconName;
  size?: number;
  style?: StyleProp<ImageStyle>;
}) {
  return (
    <Image
      source={ICONS[name]}
      style={[{ width: size, height: size, resizeMode: "contain" }, style]}
    />
  );
}
