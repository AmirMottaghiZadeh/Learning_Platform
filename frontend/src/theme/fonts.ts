import { useFonts } from "expo-font";
import { Inter_400Regular } from "@expo-google-fonts/inter/400Regular";
import { Inter_700Bold } from "@expo-google-fonts/inter/700Bold";
import { DMSans_400Regular } from "@expo-google-fonts/dm-sans/400Regular";
import { DMSans_700Bold } from "@expo-google-fonts/dm-sans/700Bold";
import { SourceSans3_400Regular } from "@expo-google-fonts/source-sans-3/400Regular";
import { SourceSans3_700Bold } from "@expo-google-fonts/source-sans-3/700Bold";
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
    Inter_400Regular,
    Inter_700Bold,
    DMSans_400Regular,
    DMSans_700Bold,
    SourceSans3_400Regular,
    SourceSans3_700Bold,
    Vazirmatn_400Regular,
    Vazirmatn_500Medium,
    Vazirmatn_600SemiBold,
    Vazirmatn_700Bold,
    Vazirmatn_800ExtraBold,
    Vazirmatn_900Black,
  });
}
