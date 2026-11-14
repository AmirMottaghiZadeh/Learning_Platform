import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** The text sizes the readers offer, as a share of the normal size: from a
 * little smaller to half again as large. */
export const TEXT_SCALES = [0.85, 0.92, 1, 1.08, 1.16, 1.25, 1.35, 1.5, 1.65] as const;
/** What the Medscape reader's "Aa" button steps through. */
export const READER_SCALES = [1, 1.12, 1.25] as const;

/** How many articles' last-read section is kept; the oldest go first. */
const MAX_REMEMBERED = 60;

type ReaderState = {
  /** text size, as a share of the normal size */
  textScale: number;
  /** article key -> index of the top-level section last read */
  lastSection: Record<string, number>;
  /** article keys, most recently read last -- keeps lastSection bounded */
  order: string[];
  cycleScale: () => void;
  setTextScale: (scale: number) => void;
  rememberSection: (key: string, index: number) => void;
};

/** Reading preferences shared by the UpToDate and Medscape readers: text
 * size, and where each article was left off so its home page can offer
 * "continue from section N". Persisted, since both outlive a session. */
export const useReader = create<ReaderState>()(
  persist(
    (set) => ({
      textScale: 1,
      lastSection: {},
      order: [],
      // the next of READER_SCALES above the current size, back to normal after the last
      cycleScale: () =>
        set((s) => ({ textScale: READER_SCALES.find((v) => v > s.textScale + 0.001) ?? READER_SCALES[0] })),
      setTextScale: (scale) => set({ textScale: Math.min(TEXT_SCALES[TEXT_SCALES.length - 1], Math.max(TEXT_SCALES[0], scale)) }),
      rememberSection: (key, index) =>
        set((s) => {
          if (s.lastSection[key] === index) return s;
          const order = [...s.order.filter((k) => k !== key), key];
          const lastSection = { ...s.lastSection, [key]: index };
          while (order.length > MAX_REMEMBERED) delete lastSection[order.shift() as string];
          return { lastSection, order };
        }),
    }),
    {
      name: "pharmenta.reader",
      version: 1,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ textScale: s.textScale, lastSection: s.lastSection, order: s.order }),
      // version 0 kept an index into READER_SCALES
      migrate: (persisted, version) => {
        const old = (persisted ?? {}) as { scaleIndex?: number; textScale?: number };
        if (version < 1) return { ...old, textScale: READER_SCALES[old.scaleIndex ?? 0] ?? 1 } as ReaderState;
        return old as ReaderState;
      },
    },
  ),
);

export function useReaderScale(): number {
  return useReader((s) => s.textScale) || 1;
}

/** The step of TEXT_SCALES nearest to `scale`. */
export function scaleStep(scale: number): number {
  let best = 0;
  TEXT_SCALES.forEach((v, i) => {
    if (Math.abs(v - scale) < Math.abs(TEXT_SCALES[best] - scale)) best = i;
  });
  return best;
}
