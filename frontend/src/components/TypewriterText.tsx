import React, {useEffect, useMemo, useState} from "react";
import {Text} from "react-native";
import type {StyleProp, TextStyle} from "react-native";

export function TypewriterText({
  text,
  style,
  delay = 0,
  speed = 12,
  instant = false,
}: {
  text: string;
  style?: StyleProp<TextStyle>;
  delay?: number;
  speed?: number;
  instant?: boolean;
}) {
  const [visibleLength, setVisibleLength] = useState(instant ? text.length : 0);
  const characters = useMemo(() => Array.from(text), [text]);

  useEffect(() => {
    if (instant) {
      setVisibleLength(characters.length);
      return;
    }

    setVisibleLength(0);
    let index = 0;
    let interval: ReturnType<typeof setInterval> | null = null;
    const timeout = setTimeout(() => {
      interval = setInterval(() => {
        index += 1;
        setVisibleLength(index);
        if (index >= characters.length && interval) clearInterval(interval);
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timeout);
      if (interval) clearInterval(interval);
    };
  }, [characters.length, delay, instant, speed, text]);

  return <Text style={style}>{characters.slice(0, visibleLength).join("")}</Text>;
}
