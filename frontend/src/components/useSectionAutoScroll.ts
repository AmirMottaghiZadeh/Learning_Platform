import {useCallback, useRef} from "react";
import type {LayoutChangeEvent, ScrollView} from "react-native";

const SCROLL_OFFSET = 12;
const SCROLL_DELAY_MS = 80;

export function useSectionAutoScroll<SectionKey extends string>() {
  const scrollRef = useRef<ScrollView | null>(null);
  const sectionPositionsRef = useRef<Partial<Record<SectionKey, number>>>({});

  const registerSection = useCallback(
    (section: SectionKey) => (event: LayoutChangeEvent) => {
      sectionPositionsRef.current[section] = event.nativeEvent.layout.y;
    },
    [],
  );

  const scrollToSection = useCallback((section: SectionKey) => {
    setTimeout(() => {
      const y = sectionPositionsRef.current[section];
      if (typeof y !== "number") return;
      scrollRef.current?.scrollTo({
        y: Math.max(0, y - SCROLL_OFFSET),
        animated: true,
      });
    }, SCROLL_DELAY_MS);
  }, []);

  return {scrollRef, registerSection, scrollToSection};
}
