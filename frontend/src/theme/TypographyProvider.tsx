import AsyncStorage from "@react-native-async-storage/async-storage";
import * as DocumentPicker from "expo-document-picker";
import { File, Paths } from "expo-file-system";
import { loadAsync } from "expo-font";
import React, { createContext, useContext, useEffect, useState } from "react";
import { Platform } from "react-native";

import { FontWeight, fontFamily } from "./fonts";

export const FONT_OPTIONS = {
  fa: [
    { id: "vazirmatn", label: "وزیرمتن" },
    { id: "yekan", label: "یکان" },
    { id: "iran-sans", label: "ایران‌سنس" },
    { id: "ir-lotus", label: "IR Lotus" },
  ],
  en: [
    { id: "inter", label: "Inter" },
    { id: "source-sans", label: "Source Sans 3" },
    { id: "dm-sans", label: "DM Sans" },
    { id: "times", label: "Times New Roman" },
    { id: "calibri", label: "Calibri" },
  ],
} as const;

export const FONT_SCALES = [0.9, 1, 1.12, 1.25] as const;
type Script = keyof typeof FONT_OPTIONS;
type FontId = (typeof FONT_OPTIONS)[Script][number]["id"];
type FontScale = (typeof FONT_SCALES)[number];
type LocalFontId = "yekan" | "iran-sans" | "ir-lotus" | "times" | "calibri";
type Fonts = Record<Script, FontId | null>;
type LocalFonts = Partial<Record<LocalFontId, string>>;

const KEY = "pharmenta.typography";
const LOCAL = {
  yekan: ["Yekan", "B Yekan", "IRYekan", "IPT Yekan"],
  "iran-sans": ["IRANSans", "IRANSansWeb", "Iran Sans", "IRANSans Regular"],
  "ir-lotus": ["IRlotus", "IR Lotus", "IRlotus Regular"],
  times: ["Times New Roman", "TimesNewRomanPSMT"],
  calibri: ["Calibri", "Calibri Regular"],
} as const satisfies Record<LocalFontId, readonly string[]>;

const BUNDLED = {
  inter: ["Inter_400Regular", "Inter_700Bold"],
  "source-sans": ["SourceSans3_400Regular", "SourceSans3_700Bold"],
  "dm-sans": ["DMSans_400Regular", "DMSans_700Bold"],
} as const;

const MAX_FONT_BYTES = 1024 * 1024;
const localIds = Object.keys(LOCAL) as LocalFontId[];
const isLocal = (id: FontId): id is LocalFontId => Object.hasOwn(LOCAL, id);

function optionFor(script: Script, value: unknown): FontId | null {
  return FONT_OPTIONS[script].find((font) => font.id === value)?.id ?? null;
}

type SavedFont = { family: string; source: string };

async function discoverFont(id: LocalFontId): Promise<string | undefined> {
  const raw = await AsyncStorage.getItem(`${KEY}.file.${id}`);
  if (raw) {
    try {
      const { family, source } = JSON.parse(raw) as SavedFont;
      if (!/^PharmentaFont\d+$/.test(family)) throw new Error("Invalid font family");
      if (Platform.OS === "web") {
        if (!/^data:[^,]*;base64,/.test(source)) throw new Error("Invalid font source");
        await loadAsync(family, source);
      } else {
        if (!/^PharmentaFont\d+\.(ttf|otf)$/.test(source)) throw new Error("Invalid font source");
        await loadAsync(family, new File(Paths.document, source).uri);
      }
      return family;
    } catch {
      // The device may have discarded a file. Try the system face on web.
    }
  }
  if (Platform.OS === "web" && typeof FontFace !== "undefined") {
    const family = `PharmentaSystem-${id}`;
    const locations = LOCAL[id].map((name) => `local("${name}")`).join(", ");
    const face = await new FontFace(family, locations).load();
    document.fonts.add(face);
    return family;
  }
  return undefined;
}

async function pickFont(id: LocalFontId): Promise<string | undefined> {
  const picked = await DocumentPicker.getDocumentAsync({
    type: Platform.OS === "web" ? [".ttf", ".otf"] : "*/*",
    copyToCacheDirectory: true,
    base64: false,
  });
  if (picked.canceled) return undefined;
  const asset = picked.assets[0];
  const extension = asset?.name.match(/\.(ttf|otf)$/i)?.[1].toLowerCase();
  if (!extension || (asset.size ?? 0) > MAX_FONT_BYTES) {
    if (Platform.OS === "web" && asset?.uri) URL.revokeObjectURL(asset.uri);
    throw new Error("Invalid font file");
  }

  const family = `PharmentaFont${Date.now()}`;
  const key = `${KEY}.file.${id}`;
  if (Platform.OS === "web") {
    try {
      if (!asset.file?.size) throw new Error("Missing font file");
      const source = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => typeof reader.result === "string" ? resolve(reader.result) : reject(new Error("Invalid font data"));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(asset.file!);
      });
      await loadAsync(family, source);
      await AsyncStorage.setItem(key, JSON.stringify({ family, source }));
    } finally {
      URL.revokeObjectURL(asset.uri);
    }
  } else {
    const original = new File(asset.uri);
    const target = new File(Paths.document, `${family}.${extension}`);
    if (!original.size || original.size > MAX_FONT_BYTES) throw new Error("Invalid font size");
    try {
      await original.copy(target);
      await loadAsync(family, target.uri);
      await AsyncStorage.setItem(key, JSON.stringify({ family, source: target.name }));
    } catch (error) {
      if (target.exists) await target.delete();
      throw error;
    }
  }
  return family;
}

type Typography = {
  ready: boolean;
  fonts: Fonts;
  scale: FontScale;
  needsFile: (id: FontId) => boolean;
  family: (script: Script, weight?: FontWeight) => string | undefined;
  setFont: (script: Script, id: FontId) => Promise<void>;
  setScale: (scale: FontScale) => Promise<void>;
};

const TypographyContext = createContext<Typography | null>(null);

export function TypographyProvider({ children }: { children: React.ReactNode }) {
  const [fonts, setFonts] = useState<Fonts>({ fa: "vazirmatn", en: "inter" });
  const [scale, updateScale] = useState<FontScale>(1);
  const [local, setLocal] = useState<LocalFonts>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function restore() {
      const choices = await AsyncStorage.multiGet([`${KEY}.fa`, `${KEY}.en`, `${KEY}.scale`]).catch(() => []);
      const resolved: LocalFonts = {};
      await Promise.all(localIds.map(async (id) => {
        resolved[id] = await discoverFont(id).catch(() => undefined);
      }));
      if (!mounted) return;
      const available = (script: Script, raw: unknown) => {
        const id = optionFor(script, raw);
        return id && (!isLocal(id) || resolved[id]) ? id : null;
      };
      setLocal(resolved);
      setFonts({ fa: available("fa", choices[0]?.[1]) ?? "vazirmatn", en: available("en", choices[1]?.[1]) ?? "inter" });
      updateScale(FONT_SCALES.find((value) => String(value) === choices[2]?.[1]) ?? 1);
      setReady(true);
    }
    void restore();
    return () => { mounted = false; };
  }, []);

  async function setFont(script: Script, id: FontId) {
    if (!optionFor(script, id)) return;
    if (isLocal(id) && !local[id]) {
      const family = await pickFont(id);
      if (!family) return;
      setLocal((prev) => ({ ...prev, [id]: family }));
    }
    await AsyncStorage.setItem(`${KEY}.${script}`, id);
    setFonts((prev) => ({ ...prev, [script]: id }));
  }

  function family(script: Script, weight: FontWeight = "400") {
    const id = fonts[script];
    if (!id) return undefined;
    if (id === "vazirmatn") return fontFamily(weight);
    if (isLocal(id)) return local[id];
    return BUNDLED[id][Number(weight) >= 700 ? 1 : 0];
  }

  async function setScale(next: FontScale) {
    await AsyncStorage.setItem(`${KEY}.scale`, String(next));
    updateScale(next);
  }

  return (
    <TypographyContext.Provider value={{ ready, fonts, scale, family, setFont, setScale, needsFile: (id) => isLocal(id) && !local[id] }}>
      {children}
    </TypographyContext.Provider>
  );
}

export function useTypography() {
  const context = useContext(TypographyContext);
  if (!context) throw new Error("useTypography must be used within TypographyProvider");
  return context;
}
