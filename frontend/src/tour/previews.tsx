import React, { useEffect, useRef } from "react";
import { AccessibilityInfo, Animated, Easing, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** A label in both languages, or one that reads the same in both (a drug name). */
export type Txt = string | { fa: string; en: string };

/** What a tour step's little animated frame shows -- what using the ringed
 * element looks like. Each kind is one looping animation. */
export type PreviewSpec =
  | { kind: "search"; term: Txt; rows: Txt[] }
  | { kind: "tap"; tiles: Txt[]; result: Txt }
  | { kind: "check"; title: Txt; sub: Txt }
  | { kind: "flip"; front: Txt; chip: Txt; back: Txt[] }
  | { kind: "list"; rows: Txt[]; highlight?: number }
  /** the bottom nav, or a screen's own switch when `items` are given */
  | { kind: "nav"; items?: Txt[] }
  | { kind: "choice"; options: Txt[]; wrong: number; correct: number }
  | { kind: "drawers" }
  | { kind: "interaction"; a: Txt; b: Txt; severity: Txt }
  | { kind: "zoom" }
  | { kind: "score"; options: Txt[] }
  | { kind: "bands"; band: Txt; rows: Txt[] }
  | { kind: "offline" };

const LOOP_MS = 4000;

/** One 0 -> 1 value, looping: every element maps it through its own
 * keyframes (`kf`), like a CSS animation. Still when motion is reduced. */
function useLoop() {
  const v = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    let loop: Animated.CompositeAnimation | null = null;
    let cancelled = false;
    AccessibilityInfo.isReduceMotionEnabled()
      .catch(() => false)
      .then((reduced) => {
        if (cancelled) return;
        if (reduced) return v.setValue(0.7);
        loop = Animated.loop(Animated.timing(v, { toValue: 1, duration: LOOP_MS, easing: Easing.linear, useNativeDriver: false }));
        loop.start();
      });
    return () => {
      cancelled = true;
      loop?.stop();
    };
  }, [v]);
  return v;
}

function kf<T extends number | string>(v: Animated.Value, input: number[], output: T[]) {
  return v.interpolate({ inputRange: input, outputRange: output as never, extrapolate: "clamp" });
}

function useTx() {
  const { isFa } = useLang();
  return (t: Txt) => (typeof t === "string" ? t : isFa ? t.fa : t.en);
}

function Line({ children, size = 11, weight = "700" as const, color }: { children: React.ReactNode; size?: number; weight?: "600" | "700" | "800" | "900"; color?: string }) {
  return (
    <AppText weight={weight} size={size} color={color} numberOfLines={1}>
      {children}
    </AppText>
  );
}

function Search({ spec }: { spec: Extract<PreviewSpec, { kind: "search" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const { row } = useLang();
  const term = tx(spec.term);
  const typed = Math.max(40, term.length * 7.5);
  return (
    <View style={{ gap: 6 }}>
      <View style={{ height: 28, borderRadius: 9, backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.trackBg, flexDirection: row, alignItems: "center", gap: 6, paddingHorizontal: 10 }}>
        <AppText muted size={12}>
          ⌕
        </AppText>
        <Animated.View style={{ width: kf(v, [0, 0.35, 1], [0, typed, typed]), overflow: "hidden" }}>
          <View style={{ width: typed }}>
            <Line size={12}>{term}</Line>
          </View>
        </Animated.View>
        <Animated.View style={{ width: 1.5, height: 14, backgroundColor: colors.accent, opacity: kf(v, [0, 0.1, 0.2, 0.3, 0.4, 1], [1, 0, 1, 0, 1, 1]) }} />
      </View>
      {spec.rows.slice(0, 3).map((r, i) => (
        <Animated.View
          key={i}
          style={{
            height: 19,
            borderRadius: 6,
            backgroundColor: colors.cardBg,
            justifyContent: "center",
            paddingHorizontal: 8,
            opacity: kf(v, [0, 0.42 + i * 0.05, 0.55 + i * 0.05, 0.92, 1], [0, 0, 1, 1, 0]),
            transform: [{ translateY: kf(v, [0, 0.42 + i * 0.05, 0.55 + i * 0.05], [8, 8, 0]) }],
          }}
        >
          <Line size={10.5}>{tx(r)}</Line>
        </Animated.View>
      ))}
    </View>
  );
}

function Tap({ spec }: { spec: Extract<PreviewSpec, { kind: "tap" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const { row } = useLang();
  return (
    <View style={{ flex: 1 }}>
      <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6 }}>
        {spec.tiles.slice(0, 4).map((tile, i) => (
          <Animated.View
            key={i}
            style={{
              width: "48%",
              height: 40,
              borderRadius: 9,
              backgroundColor: colors.cardBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              justifyContent: "flex-end",
              padding: 6,
              transform: i === 0 ? [{ scale: kf(v, [0, 0.2, 0.28, 0.36, 1], [1, 1, 0.9, 1, 1]) }] : undefined,
            }}
          >
            <Line size={10.5} weight="800">
              {tx(tile)}
            </Line>
            {i === 0 ? (
              <Animated.View
                style={{
                  position: "absolute",
                  alignSelf: "center",
                  top: 9,
                  width: 22,
                  height: 22,
                  borderRadius: 11,
                  backgroundColor: colors.accent,
                  opacity: kf(v, [0, 0.22, 0.42, 1], [0.5, 0.5, 0, 0]),
                  transform: [{ scale: kf(v, [0, 0.22, 0.42, 1], [0, 0, 2.4, 2.4]) }],
                }}
              />
            ) : null}
          </Animated.View>
        ))}
      </View>
      <Animated.View
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          bottom: 0,
          borderRadius: 10,
          backgroundColor: colors.cardBg,
          padding: 10,
          gap: 6,
          opacity: kf(v, [0, 0.34, 0.5, 0.88, 1], [0, 0, 1, 1, 0]),
          transform: [{ scale: kf(v, [0, 0.34, 0.5, 1], [0.3, 0.3, 1, 1]) }],
        }}
      >
        <Line size={11.5} weight="900" color={colors.accent}>
          {tx(spec.result)}
        </Line>
        {[0.8, 0.64, 0.72].map((w, i) => (
          <View key={i} style={{ height: 9, width: `${w * 100}%`, borderRadius: 4, backgroundColor: colors.softBg }} />
        ))}
      </Animated.View>
    </View>
  );
}

function CheckDot({ v, colors }: { v: Animated.Value; colors: ReturnType<typeof useTheme>["colors"] }) {
  return (
    <Animated.View
      style={{
        width: 22,
        height: 22,
        borderRadius: 11,
        backgroundColor: colors.accent,
        alignItems: "center",
        justifyContent: "center",
        transform: [{ scale: kf(v, [0, 0.62, 0.72, 0.8, 1], [0, 0, 1.15, 1, 1]) }],
      }}
    >
      <AppText weight="900" size={11} color={colors.onAccent}>
        ✓
      </AppText>
    </Animated.View>
  );
}

function Check({ spec }: { spec: Extract<PreviewSpec, { kind: "check" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const { row } = useLang();
  return (
    <View style={{ flex: 1, borderRadius: 10, backgroundColor: colors.cardBg, padding: 10, gap: 7 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
        <CheckDot v={v} colors={colors} />
        <View style={{ flex: 1 }}>
          <Line size={11.5} weight="900">
            {tx(spec.title)}
          </Line>
          <Line size={10} color={colors.muted}>
            {tx(spec.sub)}
          </Line>
        </View>
      </View>
      <View style={{ height: 7, borderRadius: 4, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row }}>
        <Animated.View style={{ height: "100%", borderRadius: 4, backgroundColor: colors.accent, width: kf(v, [0, 0.15, 0.65, 1], ["25%", "25%", "60%", "60%"]) }} />
      </View>
    </View>
  );
}

function Flip({ spec }: { spec: Extract<PreviewSpec, { kind: "flip" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const { row } = useLang();
  return (
    <Animated.View style={{ flex: 1, transform: [{ scaleX: kf(v, [0, 0.35, 0.45, 0.55, 1], [1, 1, 0.02, 1, 1]) }] }}>
      <Animated.View
        style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0, borderRadius: 10, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center", gap: 6, opacity: kf(v, [0, 0.449, 0.45, 1], [1, 1, 0, 0]) }}
      >
        <Line size={14} weight="900" color={colors.onAccent}>
          {tx(spec.front)}
        </Line>
        <View style={{ paddingHorizontal: 9, paddingVertical: 2, borderRadius: 999, backgroundColor: colors.onAccentChip }}>
          <Line size={10} color={colors.onAccent}>
            {tx(spec.chip)}
          </Line>
        </View>
      </Animated.View>
      <Animated.View
        style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0, borderRadius: 10, backgroundColor: colors.cardBg, padding: 10, gap: 4, opacity: kf(v, [0, 0.449, 0.45, 1], [0, 0, 1, 1]) }}
      >
        {spec.back.slice(0, 4).map((b, i) => (
          <View key={i} style={{ flexDirection: row, gap: 6, alignItems: "center" }}>
            <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: colors.accent }} />
            <Line size={11}>{tx(b)}</Line>
          </View>
        ))}
      </Animated.View>
    </Animated.View>
  );
}

function List({ spec }: { spec: Extract<PreviewSpec, { kind: "list" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  return (
    <View style={{ gap: 5 }}>
      {spec.rows.slice(0, 4).map((r, i) => (
        <Animated.View
          key={i}
          style={{
            height: 22,
            borderRadius: 7,
            justifyContent: "center",
            paddingHorizontal: 9,
            backgroundColor: i === spec.highlight ? colors.accent : colors.cardBg,
            opacity: kf(v, [0, 0.08 + i * 0.08, 0.18 + i * 0.08, 0.92, 1], [0, 0, 1, 1, 0]),
            transform: [{ translateY: kf(v, [0, 0.08 + i * 0.08, 0.18 + i * 0.08], [6, 6, 0]) }],
          }}
        >
          <Line size={10.5} weight="800" color={i === spec.highlight ? colors.onAccent : colors.ink}>
            {tx(r)}
          </Line>
        </Animated.View>
      ))}
    </View>
  );
}

function Nav({ spec }: { spec: Extract<PreviewSpec, { kind: "nav" }> }) {
  const v = useLoop();
  const { colors } = useTheme();
  const { lang, row } = useLang();
  const tx = useTx();
  const labels =
    spec.items?.map(tx) ??
    (lang === "fa" ? ["خانه", "درسنامه", "فلش‌کارت", "آزمون", "پروفایل"] : ["Home", "Lessons", "Cards", "Quiz", "Profile"]);
  const count = labels.length;
  const cell = 100 / count;
  // the pill visits the items in reading order (the nav's first four tabs),
  // resting on each, then goes back to the first
  const visits = [...Array(Math.min(count, 4)).keys()];
  const part = 1 / visits.length;
  const slot = (i: number) => (row === "row-reverse" ? count - 1 - i : i) * cell;
  return (
    <View style={{ height: 52, marginTop: 22, borderRadius: 12, backgroundColor: colors.cardBg }}>
      <Animated.View
        style={{
          position: "absolute",
          top: 8,
          width: `${cell - 1}%`,
          height: 36,
          borderRadius: 10,
          backgroundColor: colors.leitnerActiveBg,
          left: kf(
            v,
            [...visits.flatMap((j) => [j * part, j * part + part * 0.72]), 1],
            [...visits.flatMap((j) => [j, j]), 0].map((i) => `${slot(i) + 0.5}%`),
          ),
        }}
      />
      <View style={{ flexDirection: row, height: "100%" }}>
        {labels.map((l) => (
          <View key={l} style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
            <Line size={9.5} weight="800">
              {l}
            </Line>
          </View>
        ))}
      </View>
    </View>
  );
}

function Choice({ spec }: { spec: Extract<PreviewSpec, { kind: "choice" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  return (
    <View style={{ gap: 5 }}>
      {spec.options.slice(0, 4).map((o, i) => {
        const tint = i === spec.wrong ? colors.denyBg : i === spec.correct ? colors.leitnerActiveBg : colors.cardBg;
        const edge = i === spec.wrong ? colors.denyBorder : i === spec.correct ? colors.accent : colors.trackBg;
        const at = i === spec.wrong ? 0.3 : i === spec.correct ? 0.5 : 2;
        return (
          <View key={i} style={{ height: 24, borderRadius: 8, backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.trackBg, justifyContent: "center", paddingHorizontal: 9 }}>
            <Animated.View
              style={{ position: "absolute", top: -1, bottom: -1, left: -1, right: -1, borderRadius: 8, backgroundColor: tint, borderWidth: 1.5, borderColor: edge, opacity: at > 1 ? 0 : kf(v, [0, at, at + 0.06, 0.92, 1], [0, 0, 1, 1, 0]) }}
            />
            <Line size={10.5} weight="800">
              {tx(o)}
            </Line>
          </View>
        );
      })}
    </View>
  );
}

function Drawers() {
  const v = useLoop();
  const { colors } = useTheme();
  const { n, row, isFa } = useLang();
  // a card climbs from drawer 2 to 3 ("didn't know"), then comes down to 2 and 1
  const slot = (box: number) => (row === "row-reverse" ? 5 - box : box - 1) * 20 + 4;
  return (
    <View style={{ flex: 1, justifyContent: "flex-end" }}>
      <View style={{ flexDirection: row, gap: 4, height: 52 }}>
        {[1, 2, 3, 4, 5].map((b) => (
          <View key={b} style={{ flex: 1, borderRadius: 7, backgroundColor: colors.cardBg, alignItems: "center", justifyContent: "flex-end", paddingBottom: 3 }}>
            <Line size={10} weight="900" color={colors.muted}>
              {n(b)}
            </Line>
          </View>
        ))}
      </View>
      <Animated.View
        style={{
          position: "absolute",
          top: 17,
          width: "12%",
          height: 24,
          borderRadius: 5,
          backgroundColor: colors.accent,
          left: kf(v, [0, 0.15, 0.3, 0.5, 0.65, 0.8, 1], [2, 2, 3, 3, 2, 1, 1].map((b) => `${slot(b)}%`)),
        }}
      />
      <Animated.View style={{ position: "absolute", top: 0, alignSelf: "center", opacity: kf(v, [0, 0.15, 0.2, 0.45, 0.5, 1], [0, 0, 1, 1, 0, 0]) }}>
        <Line size={10} weight="900" color={colors.denyLabel}>
          {isFa ? "یادم نبود" : "Didn't know"}
        </Line>
      </Animated.View>
      <Animated.View style={{ position: "absolute", top: 0, alignSelf: "center", opacity: kf(v, [0, 0.55, 0.6, 0.9, 1], [0, 0, 1, 1, 0]) }}>
        <Line size={10} weight="900" color={colors.accent}>
          {isFa ? "یادم بود" : "Knew it"}
        </Line>
      </Animated.View>
    </View>
  );
}

function Interaction({ spec }: { spec: Extract<PreviewSpec, { kind: "interaction" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const chip = (label: string, from: number) => (
    <Animated.View
      style={{
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 999,
        backgroundColor: colors.leitnerActiveBg,
        borderWidth: 1,
        borderColor: colors.accent,
        transform: [{ translateX: kf(v, [0, 0.15, 0.4, 1], [from, from, 0, 0]) }],
        opacity: kf(v, [0, 0.15, 0.25, 0.92, 1], [0, 0, 1, 1, 0]),
      }}
    >
      <Line size={10.5} weight="800" color={colors.accent}>
        {label}
      </Line>
    </Animated.View>
  );
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: 10 }}>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {chip(tx(spec.a), -40)}
        {chip(tx(spec.b), 40)}
      </View>
      <Animated.View
        style={{
          paddingHorizontal: 12,
          paddingVertical: 4,
          borderRadius: 8,
          backgroundColor: colors.denyBg,
          borderWidth: 1,
          borderColor: colors.denyBorder,
          opacity: kf(v, [0, 0.5, 0.58, 0.92, 1], [0, 0, 1, 1, 0]),
          transform: [{ scale: kf(v, [0, 0.5, 0.58, 0.64], [0.6, 0.6, 1.1, 1]) }],
        }}
      >
        <Line size={11} weight="900" color={colors.denyLabel}>
          {tx(spec.severity)}
        </Line>
      </Animated.View>
    </View>
  );
}

function Zoom() {
  const v = useLoop();
  const { colors } = useTheme();
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <Animated.View
        style={{
          width: "70%",
          height: "100%",
          borderRadius: 8,
          backgroundColor: colors.cardBg,
          borderWidth: 1,
          borderColor: colors.trackBg,
          padding: 8,
          gap: 5,
          transform: [{ scale: kf(v, [0, 0.25, 0.45, 0.85, 1], [0.45, 0.45, 1, 1, 0.45]) }],
        }}
      >
        <View style={{ flexDirection: "row", gap: 4 }}>
          {[0, 1, 2].map((c) => (
            <View key={c} style={{ flex: 1, height: 10, borderRadius: 3, backgroundColor: colors.accent + "55" }} />
          ))}
        </View>
        {[0, 1, 2, 3].map((r) => (
          <View key={r} style={{ flexDirection: "row", gap: 4 }}>
            {[0, 1, 2].map((c) => (
              <View key={c} style={{ flex: 1, height: 8, borderRadius: 3, backgroundColor: colors.softBg }} />
            ))}
          </View>
        ))}
      </Animated.View>
      <Animated.View
        style={{
          position: "absolute",
          width: 22,
          height: 22,
          borderRadius: 11,
          backgroundColor: colors.accent,
          opacity: kf(v, [0, 0.1, 0.25, 1], [0.5, 0.5, 0, 0]),
          transform: [{ scale: kf(v, [0, 0.1, 0.25, 1], [0, 0, 2.4, 2.4]) }],
        }}
      />
    </View>
  );
}

// The score after each answer: step i shows from 0.2*i until the next step.
function scoreStep(v: Animated.Value, i: number) {
  if (i === 0) return kf(v, [0, 0.199, 0.2, 1], [1, 1, 0, 0]);
  const t = 0.2 * i;
  if (i === 3) return kf(v, [0, t - 0.001, t, 1], [0, 0, 1, 1]);
  return kf(v, [0, t - 0.001, t, t + 0.199, t + 0.2, 1], [0, 0, 1, 1, 0, 0]);
}

function Score({ spec }: { spec: Extract<PreviewSpec, { kind: "score" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  const { n, row } = useLang();
  return (
    <View style={{ flexDirection: row, gap: 10, flex: 1 }}>
      <View style={{ flex: 1, gap: 5 }}>
        {spec.options.slice(0, 3).map((o, i) => (
          <View key={i} style={{ height: 24, borderRadius: 8, backgroundColor: colors.cardBg, justifyContent: "center", paddingHorizontal: 9 }}>
            <Animated.View
              style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0, borderRadius: 8, backgroundColor: colors.leitnerActiveBg, borderWidth: 1.5, borderColor: colors.accent, opacity: kf(v, [0, 0.15 + i * 0.2, 0.2 + i * 0.2, 0.92, 1], [0, 0, 1, 1, 0]) }}
            />
            <Line size={10.5} weight="800">
              {tx(o)}
            </Line>
          </View>
        ))}
      </View>
      <View style={{ width: 64, borderRadius: 10, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" }}>
        {[0, 1, 3, 4].map((score, i) => (
          <Animated.View key={score} style={{ position: "absolute", opacity: scoreStep(v, i) }}>
            <AppText weight="900" size={22} color={colors.onAccent}>
              {n(score)}
            </AppText>
          </Animated.View>
        ))}
      </View>
    </View>
  );
}

function Bands({ spec }: { spec: Extract<PreviewSpec, { kind: "bands" }> }) {
  const v = useLoop();
  const tx = useTx();
  const { colors } = useTheme();
  return (
    <View style={{ borderRadius: 10, overflow: "hidden", backgroundColor: colors.softBg }}>
      <View style={{ backgroundColor: colors.accent, paddingHorizontal: 9, paddingVertical: 6 }}>
        <Line size={10.5} weight="900" color={colors.onAccent}>
          {tx(spec.band)}
        </Line>
      </View>
      {spec.rows.slice(0, 2).map((r, i) => (
        <Animated.View
          key={i}
          style={{ paddingHorizontal: 9, paddingVertical: 7, borderTopWidth: i ? 1 : 0, borderTopColor: colors.sheetLine, opacity: kf(v, [0, 0.15 + i * 0.15, 0.3 + i * 0.15, 0.92, 1], [0, 0, 1, 1, 0]) }}
        >
          <Line size={10.5} weight="800">
            {tx(r)}
          </Line>
        </Animated.View>
      ))}
    </View>
  );
}

function Offline() {
  const v = useLoop();
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  return (
    <View style={{ flex: 1, justifyContent: "center", gap: 8 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
        <AppText weight="900" size={16} color={colors.accent}>
          ⤓
        </AppText>
        <Line size={11} weight="800">
          {isFa ? "دانلود برای استفادهٔ آفلاین" : "Download for offline use"}
        </Line>
      </View>
      <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row }}>
        <Animated.View style={{ height: "100%", borderRadius: 4, backgroundColor: colors.accent, width: kf(v, [0, 0.1, 0.7, 1], ["0%", "0%", "100%", "100%"]) }} />
      </View>
      <Animated.View style={{ alignSelf: "center", opacity: kf(v, [0, 0.7, 0.76, 0.95, 1], [0, 0, 1, 1, 0]) }}>
        <Line size={11} weight="900" color={colors.accent}>
          {isFa ? "✓ بدون اینترنت هم باز می‌شود" : "✓ Opens without internet"}
        </Line>
      </Animated.View>
    </View>
  );
}

/** The step's frame: one preview kind, looping. */
export function Preview({ spec }: { spec: PreviewSpec }) {
  switch (spec.kind) {
    case "search":
      return <Search spec={spec} />;
    case "tap":
      return <Tap spec={spec} />;
    case "check":
      return <Check spec={spec} />;
    case "flip":
      return <Flip spec={spec} />;
    case "list":
      return <List spec={spec} />;
    case "nav":
      return <Nav spec={spec} />;
    case "choice":
      return <Choice spec={spec} />;
    case "drawers":
      return <Drawers />;
    case "interaction":
      return <Interaction spec={spec} />;
    case "zoom":
      return <Zoom />;
    case "score":
      return <Score spec={spec} />;
    case "bands":
      return <Bands spec={spec} />;
    case "offline":
      return <Offline />;
  }
}
