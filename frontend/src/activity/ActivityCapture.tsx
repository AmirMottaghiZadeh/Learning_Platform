import React, { useRef } from "react";
import { GestureResponderEvent, Platform, View } from "react-native";
import { recordClick } from "./useActivity";

export function ActivityCapture({ children }: { children: React.ReactNode }) {
  const root = useRef<View>(null);
  const capture = (event: GestureResponderEvent) => {
    const { pageX, pageY } = event.nativeEvent;
    root.current?.measureInWindow((left, top, width, height) => {
      if (width > 0 && height > 0) recordClick((pageX - left) / width * 100, (pageY - top) / height * 100, "screen", width);
    });
  };
  return <View ref={root} style={{ flex: 1 }} {...(Platform.OS === "web" ? { onPointerUp: capture as never } : { onTouchEnd: capture })}>{children}</View>;
}
