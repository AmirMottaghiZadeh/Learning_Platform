import React, { useEffect, useMemo, useRef } from "react";
import {
  Animated,
  RefreshControl,
  ScrollView,
  StyleProp,
  View,
  ViewStyle,
} from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { layout, motion } from "@/theme/tokens";
import { useNavClearance } from "@/components/BottomNav";
import { TourScrollContext, TourScroller } from "@/tour/TourContext";

type Props = {
  children: React.ReactNode;
  scroll?: boolean;
  padded?: boolean;
  refreshing?: boolean;
  onRefresh?: () => void;
  contentStyle?: StyleProp<ViewStyle>;
};

/** A screen body with the design's `fadeUp` entrance. */
export function Screen({
  children,
  scroll = true,
  padded = true,
  refreshing,
  onRefresh,
  contentStyle,
}: Props) {
  const navClearance = useNavClearance();
  const { colors } = useTheme();
  const anim = useRef(new Animated.Value(0)).current;
  const scrollRef = useRef<ScrollView>(null);
  const offset = useRef(0);
  // A guided tour's step whose element is off screen scrolls it to about a
  // third of the way down.
  const scroller = useMemo<TourScroller>(
    () => ({
      reveal: (rect) =>
        new Promise((resolve) => {
          scrollRef.current?.scrollTo({ y: Math.max(0, offset.current + rect.y - 220), animated: true });
          setTimeout(resolve, 420);
        }),
    }),
    [],
  );

  useEffect(() => {
    Animated.timing(anim, {
      toValue: 1,
      duration: motion.screen,
      useNativeDriver: true,
    }).start();
  }, [anim]);

  const animatedStyle = {
    opacity: anim,
    transform: [
      { translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [10, 0] }) },
    ],
  };

  const inner = (
    <Animated.View
      style={[
        { flex: scroll ? undefined : 1, padding: padded ? layout.screenPadding : 0 },
        animatedStyle,
        contentStyle,
      ]}
    >
      {children}
    </Animated.View>
  );

  if (!scroll) {
    return <View style={{ flex: 1, backgroundColor: colors.appBg }}>{inner}</View>;
  }

  return (
    <ScrollView
      ref={scrollRef}
      onScroll={(e) => (offset.current = e.nativeEvent.contentOffset.y)}
      scrollEventThrottle={32}
      style={{ flex: 1, backgroundColor: colors.appBg }}
      contentContainerStyle={{ paddingBottom: navClearance + 24 }}
      showsVerticalScrollIndicator={false}
      refreshControl={
        onRefresh ? (
          <RefreshControl
            refreshing={!!refreshing}
            onRefresh={onRefresh}
            tintColor={colors.accent}
          />
        ) : undefined
      }
    >
      <TourScrollContext.Provider value={scroller}>{inner}</TourScrollContext.Provider>
    </ScrollView>
  );
}
