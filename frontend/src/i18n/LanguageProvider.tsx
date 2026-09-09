import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { I18nManager } from "react-native";

import { Lang, StringKey, strings, toFaDigits } from "./strings";

const STORAGE_KEY = "pharmexa.lang";

type LanguageContextValue = {
  lang: Lang;
  dir: "rtl" | "ltr";
  isFa: boolean;
  ready: boolean;
  t: (key: StringKey) => string;
  /** Localised digits: Persian numerals in fa, ascii in en. */
  n: (value: string | number) => string;
  setLang: (lang: Lang) => void;
  toggle: () => void;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("fa");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((value) => {
        if (value === "fa" || value === "en") setLangState(value);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<LanguageContextValue>(() => {
    const isFa = lang === "fa";
    // Keep JS layout logical; RN honours `writingDirection`/`textAlign` per node.
    if (I18nManager.isRTL !== isFa) {
      try {
        I18nManager.allowRTL(isFa);
      } catch {
        /* no-op on web */
      }
    }
    const setLang = (next: Lang) => {
      setLangState(next);
      AsyncStorage.setItem(STORAGE_KEY, next).catch(() => undefined);
    };
    return {
      lang,
      dir: isFa ? "rtl" : "ltr",
      isFa,
      ready,
      t: (key: StringKey) => strings[lang][key] ?? strings.fa[key] ?? String(key),
      n: (v: string | number) => (isFa ? toFaDigits(v) : String(v)),
      setLang,
      toggle: () => setLang(isFa ? "en" : "fa"),
    };
  }, [lang, ready]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLang must be used within LanguageProvider");
  return ctx;
}
