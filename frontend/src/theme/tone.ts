import { SectionTone } from "@/api/types";
import { useTheme } from "@/theme/ThemeProvider";

/** Maps a section/severity tone to its {bg, border, label} colors -- shared
 * by drug-profile sections (contraindications, warnings, ...) and anywhere
 * else that needs the same "how alarming is this" color language. */
export function toneColors(tone: SectionTone, c: ReturnType<typeof useTheme>["colors"]) {
  switch (tone) {
    case "deny":
      return { bg: c.denyBg, border: c.denyBorder, label: c.denyLabel };
    case "boxed":
      return { bg: c.denyBg, border: c.boxedBorder, label: c.boxedInk };
    case "caution":
      return { bg: c.cautBg, border: c.cautBorder, label: c.cautLabel };
    case "special":
      return { bg: c.specBg, border: c.specBorder, label: c.specLabel };
    default:
      return { bg: "transparent", border: "transparent", label: c.accent };
  }
}
