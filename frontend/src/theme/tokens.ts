/**
 * Design tokens transcribed from `Pharmexa App v2.dc.html` (the Claude Design
 * source). Colour values are exact; CSS box-shadow strings are re-expressed as
 * React Native shadow objects.
 */

export type ThemeMode = "light" | "dark";

export interface ThemeColors {
  pageBg: string;
  appBg: string;
  cardBg: string;
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

export const THEME: Record<ThemeMode, ThemeColors> = {
  light: {
    pageBg: "#E7E4DC",
    appBg: "#EFECE4",
    cardBg: "#FFFFFF",
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
    pageBg: "#0B100F",
    appBg: "#0F1413",
    cardBg: "#171F1D",
    ink: "#EDF3F0",
    muted: "#9AACA5",
    border: "rgba(255,255,255,0.06)",
    softBg: "#141B19",
    trackBg: "#26302D",
    inputBg: "#171F1D",
    navBg: "rgba(15,20,19,0.94)",
    optBg: "#171F1D",
    accent: "#9DD4B8",
    accent2: "#7EC7A8",
    onAccent: "#0D1A15",
    onAccentSub: "rgba(13,26,21,0.75)",
    onAccentChip: "rgba(13,26,21,0.12)",
    onAccentChipBorder: "rgba(13,26,21,0.28)",
    sheetLine: "#202927",
    boxedBorder: "#EDF3F0",
    boxedInk: "#EDF3F0",
    denyBg: "#1F1615",
    denyBorder: "#3D2925",
    denyInk: "#E7D3CD",
    denyLabel: "#F0A08C",
    cautBg: "#1E1C14",
    cautBorder: "#3A3524",
    cautInk: "#E6DECB",
    cautLabel: "#E0C182",
    specBg: "#191C22",
    specBorder: "#2C3140",
    specInk: "#DCE0EC",
    specLabel: "#A6B4FF",
    proseInk: "#B4C2BC",
    flipBackBg: "#1B2422",
    leitnerActiveBg: "rgba(157,212,184,0.08)",
    flipFrontInk: "#EDF3F0",
    flipFrontSub: "rgba(237,243,240,0.72)",
    meshBg: "#0B100F",
    headerMesh: "#1D2A26",
    headerMeshGradient: ["#1D2A26", "#141C1A"],
  },
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
  bottomNavHeight: 72,
  screenPadding: 20,
} as const;

export const typography = {
  title: 26,
  h1: 22,
  h2: 20,
  h3: 17,
  body: 15,
  small: 13,
  tiny: 12,
} as const;

/** RN shadow objects approximating the design's CSS box-shadows. */
export function shadow(mode: ThemeMode) {
  const heavy = mode === "dark";
  return {
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
  pop: 220,
  flip: 500,
  ease: "cubic-bezier(0.32, 0.72, 0, 1)",
} as const;
