import React, { useEffect, useRef } from "react";
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
  const { colors } = useTheme();
  const anim = useRef(new Animated.Value(0)).current;

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
      style={{ flex: 1, backgroundColor: colors.appBg }}
      contentContainerStyle={{ paddingBottom: layout.bottomNavHeight + 24 }}
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
      {inner}
    </ScrollView>
  );
}
