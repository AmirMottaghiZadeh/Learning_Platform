import React from "react";
import { Modal, Platform, View } from "react-native";
import { WebView } from "react-native-webview";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";

import { MediaContent, mediaPage } from "./mediaPage";

/** An article image or table opened full-screen, on its own HTML page
 * (mediaPage) where it zooms and pans: an image on a dark ground, at the
 * quality it is stored in; a table at its natural width. Closed by its ×,
 * or by Back (Android's or the browser's). */
export function MediaViewer({ media, onClose }: { media: MediaContent | null; onClose: () => void }) {
  const { colors, isDark } = useTheme();
  const { t, row } = useLang();
  const insets = useSafeAreaInsets();
  useBackInterceptor(!!media, onClose);
  if (!media) return null;

  const image = media.kind === "image";
  const background = image ? "#0B0F0E" : colors.appBg;
  const html = mediaPage(media, {
    background,
    ink: colors.ink,
    muted: colors.muted,
    headerBg: colors.softBg,
    line: colors.trackBg,
    cellBg: colors.cardBg,
  });
  const onDark = image || isDark;
  const title = media.caption || (image ? t("mediaImage") : t("mediaTable"));

  return (
    <Modal visible transparent={false} animationType="fade" onRequestClose={onClose}>
      <View style={{ flex: 1, backgroundColor: background }}>
        <View
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 10,
            paddingTop: insets.top + 10,
            paddingBottom: 10,
            paddingHorizontal: 16,
            backgroundColor: image ? "rgba(255,255,255,0.06)" : colors.cardBg,
            borderBottomWidth: 1,
            borderBottomColor: image ? "rgba(255,255,255,0.08)" : colors.sheetLine,
          }}
        >
          <ChromeButton onPress={onClose} size={32}>
            <AppText weight="800" size={15} color={colors.ink}>
              ×
            </AppText>
          </ChromeButton>
          <View style={{ flex: 1 }}>
            <AppText weight="800" size={13} numberOfLines={2} color={onDark ? "#F2F5F4" : colors.ink}>
              {title}
            </AppText>
            <AppText weight="600" size={11} color={onDark ? "rgba(242,245,244,0.6)" : colors.muted}>
              {t("mediaZoomHint")}
            </AppText>
          </View>
        </View>
        <View style={{ flex: 1, paddingBottom: insets.bottom }}>
          {Platform.OS === "web" ? (
            <iframe srcDoc={html} title={title} style={{ flexGrow: 1, border: "none", width: "100%", height: "100%" }} />
          ) : (
            <WebView
              originWhitelist={["*"]}
              source={{ html }}
              scrollEnabled={false}
              style={{ flex: 1, backgroundColor: background }}
            />
          )}
        </View>
      </View>
    </Modal>
  );
}
