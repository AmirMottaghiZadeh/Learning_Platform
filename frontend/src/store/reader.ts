import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** The "Aa" steps of the article reader. */
export const READER_SCALES = [1, 1.12, 1.25] as const;

/** How many articles' last-read section is kept; the oldest go first. */
const MAX_REMEMBERED = 60;

type ReaderState = {
  scaleIndex: number;
  /** article key -> index of the top-level section last read */
  lastSection: Record<string, number>;
  /** article keys, most recently read last -- keeps lastSection bounded */
  order: string[];
  cycleScale: () => void;
  rememberSection: (key: string, index: number) => void;
};

/** Reading preferences shared by the UpToDate and Medscape readers: text
 * size, and where each article was left off so its home page can offer
 * "continue from section N". Persisted, since both outlive a session. */
export const useReader = create<ReaderState>()(
  persist(
    (set) => ({
      scaleIndex: 0,
      lastSection: {},
      order: [],
      cycleScale: () => set((s) => ({ scaleIndex: (s.scaleIndex + 1) % READER_SCALES.length })),
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
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ scaleIndex: s.scaleIndex, lastSection: s.lastSection, order: s.order }),
    },
  ),
);

export function useReaderScale(): number {
  return READER_SCALES[useReader((s) => s.scaleIndex)] ?? 1;
}
