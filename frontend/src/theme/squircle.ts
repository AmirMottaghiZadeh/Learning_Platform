import { Platform, ViewStyle } from "react-native";

// iOS has continuous corners. Browsers that implement corner-shape use
// the same silhouette, with the declared radius as the platform fallback.
export const squircle = Platform.select<ViewStyle>({
  ios: { borderCurve: "continuous" },
  web: { cornerShape: "squircle" } as ViewStyle,
  default: {},
})!;
