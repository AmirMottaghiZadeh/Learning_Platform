import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Platform, View } from "react-native";
import { WebView } from "react-native-webview";

import { uptodateApi } from "@/api/endpoints";
import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

function wrap(bodyHtml: string, ink: string, bg: string, accent: string) {
  return `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 15px/1.7 -apple-system, "Segoe UI", Roboto, sans-serif; color:${ink};
         background:${bg}; margin:0; padding:16px; }
  h1,h2,h3 { line-height:1.35; }
  a { color:${accent}; }
  table { border-collapse:collapse; width:100%; display:block; overflow-x:auto; }
  td,th { border:1px solid rgba(127,127,127,.3); padding:6px 8px; }
  img { max-width:100%; height:auto; }
  .utdGraphicWrapper, figure { overflow-x:auto; }
</style></head><body>${bodyHtml}</body></html>`;
}

export function UptodateArticleScreen() {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const goBack = useNav((s) => s.goBack);
  const id = String(useNav((s) => s.params.id ?? ""));
  const titleParam = String(useNav((s) => s.params.title ?? ""));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id],
    queryFn: () => uptodateApi.topic(id),
    enabled: !!id,
  });

  const html = data
    ? wrap(data.body_html, colors.ink, colors.cardBg, colors.accent)
    : "";

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View
        style={{
          flexDirection: row,
          alignItems: "center",
          gap: 10,
          paddingHorizontal: 18,
          paddingTop: 16,
          paddingBottom: 12,
          borderBottomWidth: 1,
          borderBottomColor: colors.sheetLine,
        }}
      >
        <ChromeButton onPress={goBack} size={30}>
          <AppText weight="800" size={15} color={colors.ink}>
            {isFa ? "›" : "‹"}
          </AppText>
        </ChromeButton>
        <AppText weight="800" size={14} numberOfLines={2} style={{ flex: 1 }}>
          {data?.title || titleParam}
        </AppText>
      </View>

      {isLoading ? (
        <LoadingState />
      ) : isError || !data ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
          <AppText muted weight="600">
            {isFa ? "بارگذاری مقاله ممکن نشد." : "Could not load the article."}
          </AppText>
        </View>
      ) : Platform.OS === "web" ? (
        <iframe
          srcDoc={html}
          style={{ flexGrow: 1, border: "none", width: "100%", height: "100%" }}
          title={data.title}
        />
      ) : (
        <WebView
          originWhitelist={["*"]}
          source={{ html }}
          style={{ flex: 1, backgroundColor: colors.cardBg }}
        />
      )}
    </View>
  );
}
