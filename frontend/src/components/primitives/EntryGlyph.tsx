import React from "react";
import { ImageStyle, StyleProp } from "react-native";
import Svg, { Path, Rect } from "react-native-svg";

import { useTheme } from "@/theme/ThemeProvider";

export type EntryGlyphName = "uptodate" | "lexicomp" | "quiz" | "flashcards";

export function EntryGlyph({ name, size = 32, style }: { name: EntryGlyphName; size?: number; style?: StyleProp<ImageStyle> }) {
  const { colors, isDark } = useTheme();
  const base = colors.headerMesh;
  const paper = colors.flipFrontInk;
  const detail = colors.accent2;
  return (
    <Svg width={size} height={size} style={style} viewBox="0 0 32 32" aria-hidden focusable={false}>
      <Rect x={2} y={2} width={28} height={28} rx={8} fill={base} />
      {name === "uptodate" ? <>
        <Path d="M8 9h16v14H8z" fill={paper} opacity={0.12} />
        <Path d="M11 11v7a5 5 0 0 0 10 0v-7" fill="none" stroke={paper} strokeWidth={2.4} strokeLinecap="round" />
        <Path d="M23 7h3v6l-1.5-1L23 13Z" fill={colors.flipFrontSub} />
      </> : null}
      {name === "lexicomp" ? <>
        <Path d="M10 8v15h10" fill="none" stroke={paper} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
        <Path d="M17 11l2-2a3 3 0 0 1 4 4l-2 2m-2-3-2 2a3 3 0 0 0 4 4l3-3" fill="none" stroke={colors.flipFrontSub} strokeWidth={1.55} strokeLinecap="round" />
      </> : null}
      {name === "quiz" ? <>
        <Path d="M9 8h10l4 4v12H9a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" fill={paper} />
        <Path d="M19 8v4h4M11 13h5m-5 4h7" fill="none" stroke={detail} strokeWidth={1.3} strokeLinecap="round" strokeLinejoin="round" />
        <Rect x={18} y={17} width={9} height={9} rx={3} fill={detail} />
        <Path d="m20 21.5 1.5 1.5 3-3" fill="none" stroke={isDark ? base : paper} strokeWidth={1.45} strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === "flashcards" ? <>
        <Rect x={9} y={8} width={16} height={12} rx={2.4} fill={paper} opacity={0.45} transform="rotate(10 17 14)" />
        <Rect x={7} y={13} width={17} height={12} rx={2.4} fill={paper} />
        <Path d="M11 17.5h9m-9 3.4h5" stroke={base} strokeWidth={1.4} strokeLinecap="round" />
      </> : null}
    </Svg>
  );
}
