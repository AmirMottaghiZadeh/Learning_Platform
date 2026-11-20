import React, { createContext, useContext } from "react";
import { StyleProp, StyleSheet, Text, TextProps, TextStyle } from "react-native";

import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { FontWeight, fontFamily } from "@/theme/fonts";
import { LRI, PDI, hasPersianLetters, isolateEnglish } from "@/utils/bidi";

type Props = TextProps & {
  weight?: FontWeight;
  size?: number;
  color?: string;
  muted?: boolean;
  center?: boolean;
  style?: StyleProp<TextStyle>;
};

/** True inside a Persian paragraph, so a nested piece of it that happens to
 * hold only English («Clonidine:» as a bold label) is still laid out as part
 * of that right-to-left paragraph. */
const InPersianParagraph = createContext(false);

/** All the text in `node`, nested pieces included. */
function textOf(node: React.ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  if (React.isValidElement<{ children?: React.ReactNode }>(node)) return textOf(node.props.children);
  return "";
}

/** `node` with the bidi layer (utils/bidi) applied to its own strings. A
 * nested AppText applies it to its own; fragments are opened. */
function isolated(node: React.ReactNode): React.ReactNode {
  if (typeof node === "string") return isolateEnglish(node);
  if (Array.isArray(node)) return node.map((child, i) => <React.Fragment key={i}>{isolated(child)}</React.Fragment>);
  if (React.isValidElement<{ children?: React.ReactNode }>(node) && node.type === React.Fragment) {
    return React.cloneElement(node, undefined, isolated(node.props.children));
  }
  return node;
}

export function AppText({
  weight = "400",
  size = 15,
  color,
  muted,
  center,
  style,
  children,
  ...rest
}: Props) {
  const { colors } = useTheme();
  const { dir } = useLang();
  const inPersian = useContext(InPersianParagraph);
  // Persian text is drawn through the bidi layer: right-to-left at its
  // base, its English isolated. English with no Persian in it, shown in the
  // Persian layout («None.» in a Persian section), is one isolate, so it reads
  // left-to-right instead of «.None». Text set to left-to-right (an English
  // title, a weight) is left as it is.
  const direction = StyleSheet.flatten(style)?.writingDirection ?? dir;
  const all = textOf(children);
  const persian = direction === "rtl" && (inPersian || hasPersianLetters(all));
  const english = direction === "rtl" && !persian && /[A-Za-z]/.test(all);

  const text = (
    <Text
      {...rest}
      style={[
        {
          fontFamily: fontFamily(weight),
          fontSize: size,
          lineHeight: Math.round(size * 1.7),
          color: color ?? (muted ? colors.muted : colors.ink),
          writingDirection: dir,
          textAlign: center ? "center" : dir === "rtl" ? "right" : "left",
        },
        style,
      ]}
    >
      {persian ? (
        isolated(children)
      ) : english ? (
        <>
          {LRI}
          {children}
          {PDI}
        </>
      ) : (
        children
      )}
    </Text>
  );
  return persian && !inPersian ? <InPersianParagraph.Provider value>{text}</InPersianParagraph.Provider> : text;
}
