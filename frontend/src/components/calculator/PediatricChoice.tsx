import React, { useState } from "react";
import { Modal, Pressable, ScrollView, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";

export type PediatricOption = { value: string; label: string; detail?: string };

export function PediatricChoice({ label, value, options, onChange, placeholder, english = false }: {
  label: string; value: string; options: PediatricOption[]; onChange: (value: string) => void;
  placeholder: string; english?: boolean;
}) {
  const [open, setOpen] = useState(false);
  useBackInterceptor(open, () => setOpen(false));
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const selected = options.find(o => o.value === value);
  return <View style={{ gap: 7 }}>
    <AppText weight="700" size={13}>{label}</AppText>
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={() => setOpen(true)}
      style={{ minHeight: 48, borderWidth: 1, borderColor: colors.trackBg, borderRadius: 13, backgroundColor: colors.inputBg, padding: 12, flexDirection: row, alignItems: "center", gap: 8 }}>
      <AppText size={13} muted={!selected} style={{ flex: 1, ...(english && selected ? { writingDirection: "ltr", textAlign: "left" } as const : {}) }}>
        {selected?.label ?? placeholder}
      </AppText>
      <AppText muted size={12}>⌄</AppText>
    </Pressable>
    <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
      <Pressable onPress={() => setOpen(false)} style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.35)", justifyContent: "flex-end" }}>
        <Pressable onPress={event => event.stopPropagation()} style={{ maxHeight: "75%", backgroundColor: colors.cardBg, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, width: "100%", maxWidth: 600, alignSelf: "center" }}>
          <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <AppText size={16} weight="800" style={{ flex: 1 }}>{label}</AppText>
            <Pressable accessibilityRole="button" accessibilityLabel={isFa ? "بستن" : "Close"} onPress={() => setOpen(false)} style={{ padding: 10 }}><AppText size={20}>×</AppText></Pressable>
          </View>
          <ScrollView keyboardShouldPersistTaps="handled">
            {options.map(option => <Pressable key={option.value} accessibilityRole="button" accessibilityState={{ selected: option.value === value }}
              onPress={() => { onChange(option.value); setOpen(false); }}
              style={{ padding: 14, minHeight: 52, borderRadius: 12, marginBottom: 8, backgroundColor: option.value === value ? colors.leitnerActiveBg : colors.softBg }}>
              <AppText weight="700" size={14} color={option.value === value ? colors.accent : colors.ink}
                style={english ? { writingDirection: "ltr", textAlign: "left" } : undefined}>{option.label}</AppText>
              {option.detail && <AppText size={12} muted>{option.detail}</AppText>}
            </Pressable>)}
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  </View>;
}
