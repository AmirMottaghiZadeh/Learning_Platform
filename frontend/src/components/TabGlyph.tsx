import React, { useEffect, useRef } from "react";
import Animated, { ReduceMotion, useAnimatedProps, useSharedValue, withSpring } from "react-native-reanimated";
import Svg, { Path, PathProps } from "react-native-svg";

import { TabKey } from "@/navigation/types";
import { useTheme } from "@/theme/ThemeProvider";
import { navigationGlyphSpring } from "@/theme/tokens";

const AnimatedPath = Animated.createAnimatedComponent(Path);
const selectSpring = { ...navigationGlyphSpring, reduceMotion: ReduceMotion.System };

function glyph(outline: string, filled: string, detail?: string) {
  const tokenize = (value: string) => value.split(" ").map((part) => /^[A-Z]$/.test(part) ? part : Number(part));
  return { outline, filled, start: tokenize(outline), end: tokenize(filled), detail };
}

// Each pair has the same commands and point order. The filled state expands
// the same silhouette instead of swapping to another SVG while it moves.
const GLYPHS = {
  dashboard: glyph(
    "M 2.8 10.5 L 12 3.4 L 21.2 10.5 L 19.3 10.5 L 19.3 19 C 19.3 20 18.7 20.6 17.7 20.6 L 14.5 20.6 L 14.5 15 L 9.5 15 L 9.5 20.6 L 6.3 20.6 C 5.3 20.6 4.7 20 4.7 19 L 4.7 10.5 Z",
    "M 2.2 10.5 L 12 2.6 L 21.8 10.5 L 20.1 10.5 L 20.1 19.3 C 20.1 20.5 19.3 21.3 18.1 21.3 L 14.5 21.3 L 14.5 15.1 L 9.5 15.1 L 9.5 21.3 L 5.9 21.3 C 4.7 21.3 3.9 20.5 3.9 19.3 L 3.9 10.5 Z",
  ),
  lessons: glyph(
    "M 4.5 4.8 C 8.2 3.7 10.3 4.4 12 6.3 C 13.7 4.4 15.8 3.7 19.5 4.8 L 19.5 18 C 16.4 17.3 14.3 17.7 12 19.8 C 9.7 17.7 7.6 17.3 4.5 18 Z",
    "M 3.4 4.3 C 7.2 2.9 10.3 3.8 12 5.9 C 13.7 3.8 16.8 2.9 20.6 4.3 L 20.6 18.9 C 16.7 18.2 14.4 18.6 12 21 C 9.6 18.6 7.3 18.2 3.4 18.9 Z",
    "M 12 6.8 V 18.2 M 6.7 10 C 7.8 9.8 8.8 10 9.8 10.5 M 14.2 10.5 C 15.2 10 16.2 9.8 17.3 10",
  ),
  clinical: glyph(
    "M 7.2 4.8 L 9.2 4.8 C 9.2 3.3 10.3 2.7 12 2.7 C 13.7 2.7 14.8 3.3 14.8 4.8 L 16.8 4.8 C 18.2 4.8 19.1 5.8 19.1 7.2 L 19.1 18.9 C 19.1 20.4 18.1 21.3 16.7 21.3 L 7.3 21.3 C 5.9 21.3 4.9 20.4 4.9 18.9 L 4.9 7.2 C 4.9 5.8 5.8 4.8 7.2 4.8 Z",
    "M 6.8 4.4 L 9 4.4 C 9 2.9 10.2 2.3 12 2.3 C 13.8 2.3 15 2.9 15 4.4 L 17.2 4.4 C 18.8 4.4 19.9 5.6 19.9 7.2 L 19.9 19 C 19.9 20.7 18.7 21.8 17.1 21.8 L 6.9 21.8 C 5.3 21.8 4.1 20.7 4.1 19 L 4.1 7.2 C 4.1 5.6 5.2 4.4 6.8 4.4 Z",
    "M 9.5 6.3 H 14.5 M 7.3 13.7 H 9.8 L 11.6 10.7 L 13.3 16.1 L 14.7 13.7 H 16.7",
  ),
  profile: glyph(
    "M 12 3.2 C 14.3 3.2 15.8 4.7 15.8 7 C 15.8 9.3 14.3 10.8 12 10.8 C 9.7 10.8 8.2 9.3 8.2 7 C 8.2 4.7 9.7 3.2 12 3.2 Z M 4.8 20.6 L 4.8 19.2 C 4.8 15.9 7.6 13.4 12 13.4 C 16.4 13.4 19.2 15.9 19.2 19.2 L 19.2 20.6 Z",
    "M 12 2.8 C 14.6 2.8 16.2 4.4 16.2 7 C 16.2 9.6 14.6 11.2 12 11.2 C 9.4 11.2 7.8 9.6 7.8 7 C 7.8 4.4 9.4 2.8 12 2.8 Z M 4 21.2 L 4 19.2 C 4 15.5 7.2 13 12 13 C 16.8 13 20 15.5 20 19.2 L 20 21.2 Z",
  ),
} satisfies Record<TabKey, ReturnType<typeof glyph>>;

export function TabGlyph({ tab, active }: { tab: TabKey; active: boolean }) {
  const { colors: { muted, accent, onAccent } } = useTheme();
  const { outline, filled, start, end, detail } = GLYPHS[tab];
  const initialPath = useRef(active ? filled : outline).current;
  const selection = useSharedValue(active ? 1 : 0);

  useEffect(() => {
    selection.value = withSpring(active ? 1 : 0, selectSpring);
  }, [active, selection]);

  // react-native-svg owns its brushes. The animation sends only geometry
  // and opacity so Reanimated's color processor never sees a brush object.
  const shell = useAnimatedProps<PathProps>(() => {
    const progress = selection.value;
    const paint = Math.min(1, Math.max(0, progress));
    const path = start.map((part, i) => typeof part === "number" ? part + ((end[i] as number) - part) * progress : part).join(" ");
    return {
      d: path,
      fillOpacity: paint,
    };
  });

  return (
    <Svg testID={`nav-glyph-${tab}`} accessible={false} width={26} height={26} viewBox="0 0 24 24">
      <AnimatedPath d={initialPath} fill={accent} stroke={active ? accent : muted}
        strokeWidth={1.55} strokeLinecap="round" strokeLinejoin="round" animatedProps={shell} />
      {detail ? <Path d={detail} fill="none" stroke={active ? onAccent : muted}
        strokeWidth={1.45} strokeLinecap="round" strokeLinejoin="round" /> : null}
    </Svg>
  );
}
