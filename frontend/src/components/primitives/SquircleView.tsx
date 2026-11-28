import React, { useState } from "react";
import { LayoutChangeEvent, Platform, StyleSheet, View, ViewProps } from "react-native";
import Svg, { Path } from "react-native-svg";

import { squircle } from "@/theme/squircle";

function continuousOutline(width: number, height: number, radius: number) {
  const r = Math.min(radius, width / 2, height / 2);
  const c = r * 0.12;
  return [
    `M ${r} 0 H ${width - r} C ${width - c} 0 ${width} ${c} ${width} ${r}`,
    `V ${height - r} C ${width} ${height - c} ${width - c} ${height} ${width - r} ${height}`,
    `H ${r} C ${c} ${height} 0 ${height - c} 0 ${height - r}`,
    `V ${r} C 0 ${c} ${c} 0 ${r} 0 Z`,
  ].join(" ");
}

function AndroidSquircle({ style, onLayout, children, ...props }: ViewProps) {
  const [{ width, height }, setSize] = useState({ width: 0, height: 0 });
  const shape = StyleSheet.flatten(style);
  const radius = shape?.borderRadius;
  const line = shape?.borderWidth ?? 0;
  const inset = line / 2;
  const canDraw = typeof radius === "number" && radius > 0 && !!shape.backgroundColor &&
    width > line && height > line;
  const layout = (event: LayoutChangeEvent) => {
    const next = event.nativeEvent.layout;
    setSize((previous) => previous.width === next.width && previous.height === next.height ? previous : { width: next.width, height: next.height });
    onLayout?.(event);
  };
  return (
    <View {...props} onLayout={layout} style={[style, canDraw && { backgroundColor: "transparent", borderColor: "transparent", elevation: 0 }]}>
      {canDraw ? (
        <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
          style={{ position: "absolute", top: -line, left: -line }}>
          <Svg width={width} height={height}>
            <Path
              d={continuousOutline(width - line, height - line, radius)}
              transform={`translate(${inset} ${inset})`}
              fill={shape.backgroundColor}
              stroke={line > 0 ? shape.borderColor : undefined}
              strokeWidth={line}
            />
          </Svg>
        </View>
      ) : null}
      {children}
    </View>
  );
}

export function SquircleView({ style, ...props }: ViewProps) {
  return Platform.OS === "android" ? <AndroidSquircle {...props} style={style} /> : <View {...props} style={[squircle, style]} />;
}
