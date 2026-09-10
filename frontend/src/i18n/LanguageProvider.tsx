import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { Lang, StringKey, strings, toFaDigits } from "./strings";

const STORAGE_KEY = "pharmexa.lang";

type LanguageContextValue = {
  lang: Lang;
  dir: "rtl" | "ltr";
  isFa: boolean;
  /**
   * `flexDirection` for a row whose children read in logical (leading→trailing)
   * order: `row-reverse` in fa so the first child sits on the right, `row` in
   * en. Applied explicitly per node because the `direction` style prop is not
   * reliable on the Android release build.
   */
  row: "row" | "row-reverse";
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
    // Direction is handled entirely in JS (per-node `textAlign` and explicit
    // `flexDirection`), never through `I18nManager` or the `direction` style
    // prop: the latter is honoured by RN web but silently ignored by the
    // Android release build, which is what made RTL "work in dev, break in the
    // APK". Keeping the native layout LTR-physical everywhere makes web and
    // native identical.
    const setLang = (next: Lang) => {
      setLangState(next);
      AsyncStorage.setItem(STORAGE_KEY, next).catch(() => undefined);
    };
    return {
      lang,
      dir: isFa ? "rtl" : "ltr",
      isFa,
      row: isFa ? "row-reverse" : "row",
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
