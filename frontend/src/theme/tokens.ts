/**
 * Design tokens: the app's palette, spacing, radii and shadows (light and
 * dark). Shadows are React Native shadow objects.
 */

export type ThemeMode = "light" | "dark";

export interface ThemeColors {
  pageBg: string;
  appBg: string;
  cardBg: string;
  cardShadow: string;
  ink: string;
  muted: string;
  border: string;
  softBg: string;
  trackBg: string;
  inputBg: string;
  navBg: string;
  optBg: string;
  accent: string;
  accent2: string;
  onAccent: string;
  onAccentSub: string;
  onAccentChip: string;
  onAccentChipBorder: string;
  sheetLine: string;
  boxedBorder: string;
  boxedInk: string;
  denyBg: string;
  denyBorder: string;
  denyInk: string;
  denyLabel: string;
  cautBg: string;
  cautBorder: string;
  cautInk: string;
  cautLabel: string;
  specBg: string;
  specBorder: string;
  specInk: string;
  specLabel: string;
  proseInk: string;
  flipBackBg: string;
  leitnerActiveBg: string;
  flipFrontInk: string;
  flipFrontSub: string;
  meshBg: string;
  /** headerMesh is a gradient in dark mode; treated as a flat colour fallback. */
  headerMesh: string;
  headerMeshGradient: [string, string];
}

const darkSurfaces = {
  pageBg: "#101814",
  appBg: "#141F1B",
  cardBg: "#1D2A24",
  softBg: "#24332C",
  inputBg: "#19251F",
  trackBg: "#3C5246",
  navBg: "rgba(29,42,36,0.96)",
  optBg: "#1D2A24",
  sheetLine: "#2C4035",
  flipBackBg: "#24332C",
  meshBg: "#101814",
};

export const THEME: Record<ThemeMode, ThemeColors> = {
  light: {
    pageBg: "#E7E4DC",
    appBg: "#EFECE4",
    cardBg: "#FFFFFF",
    cardShadow: "0 4px 12px #14201D1A",
    ink: "#14201D",
    muted: "#5F6B68",
    border: "rgba(20,32,29,0.07)",
    softBg: "#F7F5EF",
    trackBg: "#E0DBD1",
    inputBg: "#FFFFFF",
    navBg: "rgba(255,255,255,0.94)",
    optBg: "#FFFFFF",
    accent: "#0F5C52",
    accent2: "#14746A",
    onAccent: "#FFFFFF",
    onAccentSub: "rgba(255,255,255,0.85)",
    onAccentChip: "rgba(255,255,255,0.18)",
    onAccentChipBorder: "rgba(255,255,255,0.35)",
    sheetLine: "#EFECE4",
    boxedBorder: "#14201D",
    boxedInk: "#14201D",
    denyBg: "#FFF1EE",
    denyBorder: "#E8BFB4",
    denyInk: "#5B2418",
    denyLabel: "#93331F",
    cautBg: "#FFF9EF",
    cautBorder: "#EEDCBB",
    cautInk: "#6B4E12",
    cautLabel: "#8A6316",
    specBg: "#F7F3FC",
    specBorder: "#E2D6F2",
    specInk: "#3D2E52",
    specLabel: "#7B5FA8",
    proseInk: "#2A3936",
    flipBackBg: "#FFFFFF",
    leitnerActiveBg: "rgba(15,92,82,0.06)",
    flipFrontInk: "#FFFFFF",
    flipFrontSub: "rgba(255,255,255,0.75)",
    meshBg: "#E7E4DC",
    headerMesh: "#0F5C52",
    headerMeshGradient: ["#0F5C52", "#0F5C52"],
  },
  dark: {
    ...darkSurfaces,
    cardShadow: "0 4px 12px #00000052",
    ink: "#EDF6F0",
    muted: "#B3C8BB",
    border: "rgba(157,212,184,0.20)",
    accent: "#9DD4B8",
    accent2: "#7EC7A8",
    onAccent: "#17251E",
    onAccentSub: "rgba(23,37,30,0.80)",
    onAccentChip: "rgba(23,37,30,0.13)",
    onAccentChipBorder: "rgba(23,37,30,0.30)",
    boxedBorder: "#E3F3E9",
    boxedInk: "#EDF6F0",
    denyBg: "#352923",
    denyBorder: "#62433A",
    denyInk: "#FFE3DB",
    denyLabel: "#FFAC96",
    cautBg: "#332D20",
    cautBorder: "#625239",
    cautInk: "#F9ECCB",
    cautLabel: "#F2C772",
    specBg: "#292C37",
    specBorder: "#454A61",
    specInk: "#E4E9F7",
    specLabel: "#BEC9F7",
    proseInk: "#D3E2D8",
    leitnerActiveBg: "rgba(157,212,184,0.13)",
    flipFrontInk: "#F2FBF6",
    flipFrontSub: "#D2E9DD",
    headerMesh: "#23463B",
    headerMeshGradient: ["#284C3F", "#1B332B"],
  },
};

/** The background tones the learner can pick in Settings: four per theme,
 * lightest first. Each sets the surfaces behind the cards (and, in the dark
 * theme, the cards themselves, so they stay a step lighter than what is
 * behind them). Index DEFAULT_TONE is the theme as designed. */
export type ToneColors = Pick<
  ThemeColors,
  "pageBg" | "appBg" | "softBg" | "sheetLine" | "meshBg" | "navBg"
> & Partial<Pick<ThemeColors, "cardBg" | "inputBg" | "optBg" | "flipBackBg" | "trackBg">>;

export const DEFAULT_TONE = 1;

export const BG_TONES: Record<ThemeMode, ToneColors[]> = {
  light: [
    { pageBg: "#F1EFE9", appBg: "#F8F7F3", softBg: "#FBFAF7", sheetLine: "#F1EFE9", meshBg: "#F1EFE9", navBg: "rgba(255,255,255,0.94)" },
    { pageBg: "#E7E4DC", appBg: "#EFECE4", softBg: "#F7F5EF", sheetLine: "#EFECE4", meshBg: "#E7E4DC", navBg: "rgba(255,255,255,0.94)" },
    { pageBg: "#DCD6C8", appBg: "#E5E0D4", softBg: "#F2EFE7", sheetLine: "#E8E4DA", meshBg: "#DCD6C8", navBg: "rgba(255,255,255,0.94)" },
    { pageBg: "#CCC4B1", appBg: "#D8D0BF", softBg: "#ECE8DE", sheetLine: "#E1DCD0", meshBg: "#CCC4B1", navBg: "rgba(255,255,255,0.95)" },
  ],
  dark: [
    {
      pageBg: "#1B2621", appBg: "#202E27", softBg: "#2A3A31", sheetLine: "#354B3F", meshBg: "#1B2621",
      navBg: "rgba(38,53,44,0.96)", cardBg: "#26352C", inputBg: "#222F28", optBg: "#26352C", flipBackBg: "#2A3A31", trackBg: "#496052",
    },
    darkSurfaces,
    {
      pageBg: "#0C120F", appBg: "#101915", softBg: "#1D2B24", sheetLine: "#25362D", meshBg: "#0C120F",
      navBg: "rgba(24,36,30,0.96)", cardBg: "#18241E", inputBg: "#151F19", optBg: "#18241E", flipBackBg: "#1D2B24", trackBg: "#34493E",
    },
    {
      pageBg: "#080D0A", appBg: "#0B120E", softBg: "#17231D", sheetLine: "#203128", meshBg: "#080D0A",
      navBg: "rgba(18,28,23,0.97)", cardBg: "#121C17", inputBg: "#101913", optBg: "#121C17", flipBackBg: "#17231D", trackBg: "#2F4238",
    },
  ],
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 8,
  input: 14,
  chip: 999,
  card: 18,
  btn: 16,
  tile: 20,
  shell: 28,
} as const;

export const layout = {
  appMaxWidth: 430,
  contentMaxWidth: 1120,
  bottomNavHeight: 72,
  screenPadding: 20,
} as const;

/** RN shadow objects approximating the design's CSS box-shadows. */
export function shadow(mode: ThemeMode) {
  const heavy = mode === "dark";
  return {
    surface: { boxShadow: THEME[mode].cardShadow },
    raised: {
      shadowColor: "#000",
      shadowOpacity: heavy ? 0.5 : 0.1,
      shadowRadius: heavy ? 30 : 18,
      shadowOffset: { width: 0, height: heavy ? 12 : 6 },
      elevation: heavy ? 12 : 4,
    },
    raisedSm: {
      shadowColor: "#000",
      shadowOpacity: heavy ? 0.4 : 0.06,
      shadowRadius: 2,
      shadowOffset: { width: 0, height: 1 },
      elevation: 1,
    },
    glow: {
      shadowColor: mode === "dark" ? "#9DD4B8" : "#0F5C52",
      shadowOpacity: mode === "dark" ? 0.14 : 0.22,
      shadowRadius: mode === "dark" ? 26 : 16,
      shadowOffset: { width: 0, height: mode === "dark" ? 10 : 6 },
      elevation: 6,
    },
    shell: {
      shadowColor: "#123B36",
      shadowOpacity: 0.16,
      shadowRadius: 70,
      shadowOffset: { width: 0, height: 30 },
      elevation: 20,
    },
  };
}

export const motion = {
  screen: 350,
  navigationFade: 120,
  navigationSlide: 180,
  pop: 220,
  flip: 500,
  ease: "cubic-bezier(0.32, 0.72, 0, 1)",
} as const;
