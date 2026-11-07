import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** One highlight in an article: where it sits in the article's text (the
 * characters of its body, in order, without the outline numbers the reader
 * adds), its colour, and a check of the text it covered -- so a highlight
 * whose article has since been revised is skipped instead of landing on the
 * wrong words. */
export type Highlight = {
  id: string;
  start: number;
  end: number;
  color: HighlightColor;
  /** djb2 hash of the highlighted text, in base 36 */
  check: string;
};

export const HIGHLIGHT_COLORS = ["yellow", "green", "blue", "pink", "orange"] as const;
export type HighlightColor = (typeof HIGHLIGHT_COLORS)[number];

/** Paint per colour: the light theme's, then the dark theme's. */
export const HIGHLIGHT_PAINT: Record<HighlightColor, [string, string]> = {
  yellow: ["#FFE98A", "rgba(255,214,64,0.38)"],
  green: ["#BDEBC4", "rgba(110,210,130,0.34)"],
  blue: ["#BFDDFB", "rgba(110,170,255,0.36)"],
  pink: ["#F8C6DB", "rgba(255,130,180,0.34)"],
  orange: ["#FFD2AA", "rgba(255,160,80,0.36)"],
};

export type FavoriteArticle = {
  /** "utd" today; the key leaves room for the other readers */
  source: "utd" | "medscape";
  kind?: "disease" | "guideline";
  id: string;
  title: string;
  section: string;
  /** ms since the epoch */
  addedAt: number;
};

type LibraryState = {
  favorites: FavoriteArticle[];
  /** article key ("utd:<id>") -> its highlights */
  highlights: Record<string, Highlight[]>;
  toggleFavorite: (article: Omit<FavoriteArticle, "addedAt">) => void;
  setHighlights: (key: string, items: Highlight[]) => void;
};

/** The learner's own marks on the reference articles: favourites and
 * highlights. Kept on this device (persisted), never sent anywhere. */
export const useLibrary = create<LibraryState>()(
  persist(
    (set) => ({
      favorites: [],
      highlights: {},
      toggleFavorite: (article) =>
        set((s) => {
          const has = s.favorites.some((f) => f.source === article.source && f.id === article.id);
          return {
            favorites: has
              ? s.favorites.filter((f) => !(f.source === article.source && f.id === article.id))
              : [{ ...article, addedAt: Date.now() }, ...s.favorites],
          };
        }),
      setHighlights: (key, items) =>
        set((s) => {
          const highlights = { ...s.highlights };
          if (items.length) highlights[key] = items;
          else delete highlights[key];
          return { highlights };
        }),
    }),
    {
      name: "pharmenta.library",
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ favorites: s.favorites, highlights: s.highlights }),
    },
  ),
);

export function useIsFavorite(source: FavoriteArticle["source"], id: string): boolean {
  return useLibrary((s) => s.favorites.some((f) => f.source === source && f.id === id));
}
