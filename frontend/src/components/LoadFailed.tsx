import React from "react";
import { Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** In place of a list that came back empty or failed to load: says so and
 * offers a retry, rather than leaving a blank space that looks like there
 * is simply nothing there. */
export function LoadFailed({ message, onRetry, busy }: { message: string; onRetry: () => void; busy?: boolean }) {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <View style={{ alignItems: "center", paddingVertical: 36, gap: 12 }}>
      <AppText muted weight="600" size={13} center>
        {message}
      </AppText>
      <Pressable
        onPress={onRetry}
        disabled={busy}
        style={{
          paddingHorizontal: 18,
          paddingVertical: 9,
          borderRadius: 12,
          backgroundColor: colors.accent,
          opacity: busy ? 0.6 : 1,
        }}
      >
        <AppText weight="800" size={13} color={colors.onAccent}>
          {busy ? "…" : t("retry")}
        </AppText>
      </Pressable>
    </View>
  );
}
