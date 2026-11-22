import AsyncStorage from "@react-native-async-storage/async-storage";
import { loadAsync } from "expo-font";
import React, { createContext, useContext, useEffect, useState } from "react";

import { READING_SIZE_OPTIONS, useReader } from "@/store/reader";
import { FontWeight, fontFamily } from "./fonts";

export const FONT_OPTIONS = {
  fa: [
    { id: "vazirmatn", label: "وزیرمتن" },
    { id: "estedad", label: "استعداد" },
    { id: "alexandria", label: "اسکندریه" },
    { id: "iran-sans", label: "ایران سانس" },
    { id: "noto-arabic", label: "نوتو سنس عربی" },
  ],
  en: [
    { id: "inter", label: "Inter" },
    { id: "source-sans", label: "Source Sans 3" },
    { id: "dm-sans", label: "DM Sans" },
    { id: "libre-baskerville", label: "Libre Baskerville" },
    { id: "carlito", label: "Carlito" },
  ],
} as const;

type Script = keyof typeof FONT_OPTIONS;
type FontId = (typeof FONT_OPTIONS)[Script][number]["id"];
type Fonts = Record<Script, FontId>;

const KEY = "pharmenta.typography";
const LEGACY_SCALE_KEY = KEY + ".scale";
const IRANIAN_SANS = "PharmentaIranianSans";
export const IRANIAN_SANS_REGULAR = IRANIAN_SANS + "Regular";
const DEFAULT_FONTS: Fonts = { fa: "estedad", en: "inter" };
const FALLBACK_FONTS: Fonts = { fa: "vazirmatn", en: "inter" };
const LEGACY_CHOICES: Partial<Record<string, FontId>> = {
  yekan: "estedad",
  "readex-pro": "iran-sans",
  "ir-lotus": "noto-arabic",
  times: "libre-baskerville",
  calibri: "carlito",
};

const ADDITIONAL_FACES = {
  estedad: ["PharmentaEstedad", require("../../assets/fonts/Estedad/Estedad-Regular.ttf"), require("../../assets/fonts/Estedad/Estedad-Bold.ttf")],
  alexandria: ["PharmentaAlexandria", require("../../assets/fonts/Alexandria/Alexandria-Regular.ttf"), require("../../assets/fonts/Alexandria/Alexandria-Bold.ttf")],
  "iran-sans": [IRANIAN_SANS, require("../../assets/fonts/IranianSans/IranianSans-Regular.ttf")],
  "noto-arabic": ["PharmentaNotoArabic", require("../../assets/fonts/NotoSansArabic/NotoSansArabic-Regular.ttf"), require("../../assets/fonts/NotoSansArabic/NotoSansArabic-Bold.ttf")],
  "libre-baskerville": ["PharmentaLibreBaskerville", require("../../assets/fonts/LibreBaskerville/LibreBaskerville-Regular.ttf"), require("../../assets/fonts/LibreBaskerville/LibreBaskerville-Bold.ttf")],
  carlito: ["PharmentaCarlito", require("../../assets/fonts/Carlito/Carlito-Regular.ttf"), require("../../assets/fonts/Carlito/Carlito-Bold.ttf")],
} as const;

const BUNDLED_FACES = {
  inter: ["Inter_400Regular", "Inter_700Bold"],
  "source-sans": ["SourceSans3_400Regular", "SourceSans3_700Bold"],
  "dm-sans": ["DMSans_400Regular", "DMSans_700Bold"],
} as const;

function additionalFace(id: FontId) {
  return id in ADDITIONAL_FACES ? ADDITIONAL_FACES[id as keyof typeof ADDITIONAL_FACES] : undefined;
}

async function loadFont(id: FontId) {
  const face = additionalFace(id);
  if (face) {
    const [family, regular, bold] = face;
    await loadAsync({ [family + "Regular"]: regular, ...(bold ? { [family + "Bold"]: bold } : {}) });
  }
}

function availableFont(script: Script, saved: string | null | undefined): FontId {
  const value = saved ? (LEGACY_CHOICES[saved] ?? saved) : null;
  return FONT_OPTIONS[script].find(({ id }) => id === value)?.id ?? DEFAULT_FONTS[script];
}

type Typography = {
  ready: boolean;
  fonts: Fonts;
  family: (script: Script, weight?: FontWeight) => string;
  setFont: (script: Script, id: FontId) => Promise<void>;
};

const TypographyContext = createContext<Typography | null>(null);

export function TypographyProvider({ children }: { children: React.ReactNode }) {
  const [fonts, setFonts] = useState<Fonts>(DEFAULT_FONTS);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function restore() {
      const choices = await AsyncStorage.multiGet([KEY + ".fa", KEY + ".en", LEGACY_SCALE_KEY]).catch(() => []);
      const fontFor = async (script: Script, index: number) => {
        const selection = availableFont(script, choices[index]?.[1]);
        try {
          await loadFont(selection);
          return selection;
        } catch {
          const defaultFont = DEFAULT_FONTS[script];
          if (selection === defaultFont) return FALLBACK_FONTS[script];
          return loadFont(defaultFont).then(() => defaultFont, () => FALLBACK_FONTS[script]);
        }
      };
      const [fa, en] = await Promise.all([fontFor("fa", 0), fontFor("en", 1)]);
      const previousScale = READING_SIZE_OPTIONS.find((value) => String(value) === choices[2]?.[1]);
      if (previousScale !== undefined) {
        try {
          if (!useReader.persist.hasHydrated()) await useReader.persist.rehydrate();
          await useReader.getState().setTextScale(previousScale);
          await AsyncStorage.removeItem(LEGACY_SCALE_KEY);
        } catch {
          // Keep the saved preference available for the next launch.
        }
      }
      if (!mounted) return;
      setFonts({ fa, en });
      setReady(true);
    }
    void restore();
    return () => { mounted = false; };
  }, []);

  async function setFont(script: Script, id: FontId) {
    if (!FONT_OPTIONS[script].some((option) => option.id === id)) return;
    await loadFont(id);
    await AsyncStorage.setItem(KEY + "." + script, id);
    setFonts((prev) => ({ ...prev, [script]: id }));
  }

  function family(script: Script, weight: FontWeight = "400") {
    const id = fonts[script];
    if (id === "vazirmatn") return fontFamily(weight);
    const bold = Number(weight) >= 700;
    const face = additionalFace(id);
    if (face) return face[0] + (bold && face[2] ? "Bold" : "Regular");
    return BUNDLED_FACES[id as keyof typeof BUNDLED_FACES][bold ? 1 : 0];
  }

  return (
    <TypographyContext.Provider value={{ ready, fonts, family, setFont }}>
      {children}
    </TypographyContext.Provider>
  );
}

export function useTypography() {
  const context = useContext(TypographyContext);
  if (!context) throw new Error("useTypography must be used within TypographyProvider");
  return context;
}
