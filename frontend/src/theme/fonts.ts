import { useFonts } from "expo-font";
import {
  Vazirmatn_400Regular,
  Vazirmatn_500Medium,
  Vazirmatn_600SemiBold,
  Vazirmatn_700Bold,
  Vazirmatn_800ExtraBold,
  Vazirmatn_900Black,
} from "@expo-google-fonts/vazirmatn";

export const FONT_BY_WEIGHT = {
  "400": "Vazirmatn_400Regular",
  "500": "Vazirmatn_500Medium",
  "600": "Vazirmatn_600SemiBold",
  "700": "Vazirmatn_700Bold",
  "800": "Vazirmatn_800ExtraBold",
  "900": "Vazirmatn_900Black",
} as const;

export type FontWeight = keyof typeof FONT_BY_WEIGHT;

export function fontFamily(weight: FontWeight | number | string = "400"): string {
  const key = String(weight) as FontWeight;
  return FONT_BY_WEIGHT[key] ?? FONT_BY_WEIGHT["400"];
}

export function useAppFonts() {
  return useFonts({
    Vazirmatn_400Regular,
    Vazirmatn_500Medium,
    Vazirmatn_600SemiBold,
    Vazirmatn_700Bold,
    Vazirmatn_800ExtraBold,
    Vazirmatn_900Black,
  });
}
