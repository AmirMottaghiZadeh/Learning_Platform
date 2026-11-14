import React, { useEffect, useRef, useState } from "react";
import { Animated, Easing, Pressable, StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";

import { Rect, useTourContext } from "./TourContext";
import { Preview } from "./previews";
import { TOURS, TourKey } from "./tours";

// How long a step stays before the tour moves on by itself.
const STEP_MS = 5500;
const RING_PAD = 6;
const CARD_MAX_W = 380;

/** The playing tour, over everything: a ring around the step's element, a
 * card with the step's preview, title and line, and segments that fill as
 * the tour moves on by itself -- like stories. Tapping the preview pauses
 * it; Back or "رد شدن" ends it. */
export function TourOverlay() {
  const tour = useTourContext();
  if (!tour?.active) return null;
  return <TourRun key={tour.active} tourKey={tour.active} />;
}

function TourRun({ tourKey }: { tourKey: TourKey }) {
  const tour = useTourContext()!;
  const steps = TOURS[tourKey];
  const { isFa, row } = useLang();
  const { colors, shadows } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: W, height: H } = useWindowDimensions();

  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const [cardH, setCardH] = useState(300);
  const [paused, setPaused] = useState(false);
  const step = steps[index];
  const last = index === steps.length - 1;

  const next = () => (last ? tour.finish() : setIndex((i) => i + 1));
  useBackInterceptor(true, tour.finish);

  // Find the step's element, scrolled into view if it is off screen.
  useEffect(() => {
    let alive = true;
    (async () => {
      const target = step.target ? tour.target(step.target) : undefined;
      if (!target) return alive && setRect(null);
      let r = await target.measure();
      // a target taller than the screen only needs its top in view
      const visible = (q: Rect | null) => !!q && q.y >= insets.top + 40 && (q.y + q.h <= H - 100 || q.y <= H * 0.45);
      if (r && !visible(r) && target.reveal) {
        await target.reveal(r);
        r = await target.measure();
      }
      if (r) {
        // the ring stays on screen
        const top = Math.max(r.y, insets.top + RING_PAD + 4);
        const bottom = Math.min(r.y + r.h, H - insets.bottom - RING_PAD - 4);
        r = { ...r, y: top, h: Math.max(bottom - top, 24) };
      }
      if (alive) setRect(r);
    })();
    return () => {
      alive = false;
    };
  }, [index, step.target, tour, H, insets.top]);

  // The ring glides from element to element.
  const ring = useRef({
    x: new Animated.Value(W / 2),
    y: new Animated.Value(H / 2),
    w: new Animated.Value(0),
    h: new Animated.Value(0),
  }).current;
  useEffect(() => {
    if (!rect) return;
    const to = { x: rect.x - RING_PAD, y: rect.y - RING_PAD, w: rect.w + RING_PAD * 2, h: rect.h + RING_PAD * 2 };
    Animated.parallel(
      (Object.keys(to) as (keyof typeof to)[]).map((k) =>
        Animated.timing(ring[k], { toValue: to[k], duration: 460, easing: Easing.out(Easing.cubic), useNativeDriver: false }),
      ),
    ).start();
  }, [rect, ring]);

  // A soft pulse around the ring.
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(Animated.timing(pulse, { toValue: 1, duration: 1800, easing: Easing.out(Easing.quad), useNativeDriver: false }));
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  // Each step's segment fills over STEP_MS, then the tour moves on.
  const progress = useRef(new Animated.Value(0)).current;
  const done = useRef(0);
  useEffect(() => {
    const id = progress.addListener(({ value }) => (done.current = value));
    return () => progress.removeListener(id);
  }, [progress]);
  useEffect(() => {
    progress.setValue(0);
    done.current = 0;
    setPaused(false);
  }, [index, progress]);
  useEffect(() => {
    if (paused) {
      progress.stopAnimation();
      return;
    }
    const anim = Animated.timing(progress, {
      toValue: 1,
      duration: STEP_MS * (1 - done.current),
      easing: Easing.linear,
      useNativeDriver: false,
    });
    anim.start(({ finished }) => finished && next());
    return () => anim.stop();
    // `next` closes over `index` and `last`, both in the deps below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, paused]);

  // The card sits below the element, or above it, or -- over a tall
  // element -- at the bottom of the screen.
  const cardW = Math.min(W - 32, CARD_MAX_W);
  let cardTop = (H - cardH) / 2;
  if (rect) {
    const below = rect.y + rect.h + RING_PAD + 14;
    const above = rect.y - RING_PAD - 14 - cardH;
    const floor = H - insets.bottom - 12 - cardH;
    cardTop = below <= floor ? below : above >= insets.top + 8 ? above : floor;
  }

  const [title, body] = isFa ? step.fa : step.en;
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
      {/* a light veil that keeps taps off the screen underneath */}
      <View style={[StyleSheet.absoluteFill, { backgroundColor: "rgba(4,10,9,0.22)" }]} onStartShouldSetResponder={() => true} />
      {rect ? (
        <Animated.View
          pointerEvents="none"
          style={{
            position: "absolute",
            left: ring.x,
            top: ring.y,
            width: ring.w,
            height: ring.h,
            borderRadius: 18,
            borderWidth: 2.5,
            borderColor: colors.accent,
          }}
        >
          <View style={{ position: "absolute", top: -5, left: -5, right: -5, bottom: -5, borderRadius: 22, borderWidth: 3, borderColor: "#FFFFFF" }} />
          <Animated.View
            style={{
              position: "absolute",
              top: -8,
              left: -8,
              right: -8,
              bottom: -8,
              borderRadius: 24,
              borderWidth: 6,
              borderColor: colors.accent,
              opacity: pulse.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0] }),
              transform: [{ scale: pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.06] }) }],
            }}
          />
        </Animated.View>
      ) : null}

      <View
        accessibilityViewIsModal
        accessibilityLabel={title}
        onLayout={(e) => setCardH(e.nativeEvent.layout.height)}
        style={[
          {
            position: "absolute",
            top: cardTop,
            left: (W - cardW) / 2,
            width: cardW,
            padding: 14,
            gap: 10,
            borderRadius: 20,
            backgroundColor: colors.cardBg,
          },
          shadows.raised,
        ]}
      >
        <View style={{ flexDirection: row, gap: 4 }}>
          {steps.map((_, i) => (
            <View key={i} style={{ flex: 1, height: 4, borderRadius: 2, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row }}>
              <Animated.View
                style={{
                  height: "100%",
                  borderRadius: 2,
                  backgroundColor: colors.accent,
                  width: i < index ? "100%" : i > index ? "0%" : progress.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] }),
                }}
              />
            </View>
          ))}
        </View>

        <Pressable
          onPress={() => setPaused((p) => !p)}
          accessibilityRole="button"
          accessibilityLabel={isFa ? "مکث یا ادامهٔ راهنما" : "Pause or resume the tour"}
          style={{ height: 122, borderRadius: 14, borderWidth: 1, borderColor: colors.trackBg, backgroundColor: colors.softBg, padding: 12, overflow: "hidden" }}
        >
          <Preview key={`${tourKey}-${index}`} spec={step.preview} />
          {paused ? (
            <View style={{ position: "absolute", top: 8, left: 8, paddingHorizontal: 9, paddingVertical: 3, borderRadius: 999, backgroundColor: colors.ink }}>
              <AppText weight="800" size={10.5} color={colors.cardBg}>
                {isFa ? "مکث" : "Paused"}
              </AppText>
            </View>
          ) : null}
        </Pressable>

        <View style={{ gap: 3 }}>
          <AppText weight="900" size={16}>
            {title}
          </AppText>
          <AppText weight="600" size={13} muted style={{ lineHeight: 21 }}>
            {body}
          </AppText>
        </View>

        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <Pressable onPress={tour.finish} accessibilityRole="button" hitSlop={8} style={{ paddingVertical: 8, paddingHorizontal: 4 }}>
            <AppText weight="700" size={12.5} muted>
              {isFa ? "رد شدن" : "Skip"}
            </AppText>
          </Pressable>
          <Pressable
            onPress={next}
            accessibilityRole="button"
            style={({ pressed }) => ({
              height: 38,
              paddingHorizontal: 18,
              borderRadius: 12,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: colors.accent,
              opacity: pressed ? 0.85 : 1,
            })}
          >
            <AppText weight="800" size={13} color={colors.onAccent}>
              {last ? (isFa ? "شروع کن" : "Got it") : isFa ? "بعدی" : "Next"}
            </AppText>
          </Pressable>
        </View>
      </View>
    </View>
  );
}
