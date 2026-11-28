import React, { useEffect, useMemo, useRef } from "react";
import { Modal, Platform, Pressable, ScrollView, View, useWindowDimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import Svg, { Path } from "react-native-svg";
import type { UptodateArticle } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { HeaderMesh } from "@/components/HeaderMesh";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { LangToggleButton } from "@/components/ScreenChrome";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { useNav } from "@/store/nav";
import { useIsFavorite, useLibrary } from "@/store/library";
import { layout, radius, spacing } from "@/theme/tokens";
import { referenceCalculatorPage } from "@/utils/referenceCalculatorPage";
import type { ReferenceContent } from "@/utils/referenceContent";

/** Selected design 2: a bottom sheet, without article-only tools or progress. */
export function ReferenceContentSheet({ article, content, onClose }: {
  article: UptodateArticle; content: Exclude<ReferenceContent, { kind: "article" }>; onClose: () => void;
}) {
  const { colors } = useTheme();
  const { isFa, row, n } = useLang();
  const { height } = useWindowDimensions();
  const navigate = useNav(s => s.navigate);
  const toggleFavorite = useLibrary(s => s.toggleFavorite);
  const favorite = useIsFavorite("utd", article.id);
  const iframe = useRef<HTMLIFrameElement | null>(null);
  const isCalculator = content.kind === "calculator";
  const label = isFa ? isCalculator ? "ابزار محاسبه" : "فهرست موضوعی" : isCalculator ? "Calculator" : "Topic directory";
  const html = useMemo(() => isCalculator ? referenceCalculatorPage(article.body_html, colors, isFa ? "fa" : "en") : "", [article.body_html, colors, isCalculator, isFa]);
  const openTopic = (id: string, title = "") => { if (/^\d+$/.test(id) && id !== article.id) navigate("uptodateArticle", { id, title }); };
  const receive = (data: string) => {
    try { const message = JSON.parse(data); if (message?.type === "reference-topic" && typeof message.id === "string") openTopic(message.id); }
    catch { /* Unrelated source messages cannot invoke app operations. */ }
  };
  useEffect(() => {
    if (Platform.OS !== "web" || !isCalculator) return;
    const listener = (event: MessageEvent) => { if (event.source === iframe.current?.contentWindow && typeof event.data === "string") receive(event.data); };
    window.addEventListener("message", listener);
    return () => window.removeEventListener("message", listener);
  }, [isCalculator, article.id]);
  const title = article.title.replace(/^Calculator:\s*/i, "");
  return <View style={{ flex: 1, backgroundColor: colors.appBg }}>
    <View style={{ height: 100 }}><HeaderMesh><View style={{ padding: spacing.xl }}><AppText color="#FFFFFF" weight="800" size={17}>{isFa ? "منابع بالینی" : "Clinical references"}</AppText></View></HeaderMesh></View>
    <View style={{ padding: spacing.xl, gap: spacing.sm }}>
      <AppText weight="800" size={19}>{label}</AppText>
      <AppText muted size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{title}</AppText>
    </View>
    <Modal visible transparent animationType="slide" onRequestClose={onClose}>
      <View style={{ flex: 1, justifyContent: "flex-end", alignItems: "center", backgroundColor: "rgba(11,16,15,0.32)" }}>
        <Pressable testID="reference-sheet-backdrop" accessibilityRole="button" accessibilityLabel={isFa ? "بستن و بازگشت" : "Close and go back"} onPress={onClose} style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0 }} />
        <SafeAreaView testID="reference-content-sheet" edges={["bottom", "left", "right"]} style={{ width: "100%", maxWidth: layout.appMaxWidth, maxHeight: height * 0.9,
          ...(isCalculator ? { height: height * 0.86 } : {}), backgroundColor: colors.cardBg, borderTopLeftRadius: radius.shell, borderTopRightRadius: radius.shell, overflow: "hidden" }}>
          <View style={{ paddingHorizontal: spacing.xl, paddingTop: spacing.md, gap: spacing.md }}>
            <View style={{ width: 36, height: 4, borderRadius: 4, backgroundColor: colors.trackBg, alignSelf: "center" }} />
            <View style={{ flexDirection: row, alignItems: "center", gap: spacing.sm }}>
              <AppText muted size={12} style={{ flex: 1 }}>{label} · UpToDate</AppText>
              <ThemeToggleButton variant="soft" size={44} /><LangToggleButton size={44} />
              <Pressable testID="reference-sheet-close" onPress={onClose} accessibilityRole="button" accessibilityLabel={isFa ? "بستن" : "Close"} style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center" }}>
                <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colors.ink} strokeWidth={1.7}><Path d="m6 6 12 12M6 18 18 6" strokeLinecap="round" /></Svg>
              </Pressable>
            </View>
            <AppText accessibilityRole="header" aria-level={1} weight="800" size={20} style={{ writingDirection: "ltr", textAlign: "left" }}>{title}</AppText>
            {!isCalculator ? <AppText muted size={13}>{isFa ? `این عنوان شامل ${n(content.links.length)} زیرموضوع است؛ برای ادامه یکی را انتخاب کنید.` : `Choose one of ${content.links.length} subtopics to continue.`}</AppText> : null}
          </View>
          {isCalculator ? <View testID="reference-calculator" style={{ flex: 1, minHeight: 180, marginHorizontal: spacing.lg, marginTop: spacing.md }}>
            {Platform.OS === "web" ? <iframe ref={iframe} srcDoc={html} sandbox="allow-scripts" title={title} referrerPolicy="no-referrer" style={{ border: "none", flex: 1, width: "100%", height: "100%", backgroundColor: colors.cardBg }} />
              : <WebView source={{ html }} originWhitelist={["about:blank", "about:srcdoc"]} javaScriptEnabled domStorageEnabled={false} sharedCookiesEnabled={false} thirdPartyCookiesEnabled={false}
                allowFileAccess={false} mixedContentMode="never" javaScriptCanOpenWindowsAutomatically={false} setSupportMultipleWindows={false}
                onShouldStartLoadWithRequest={request => request.url === "about:blank" || request.url.startsWith("about:srcdoc") || request.url.startsWith("data:text/html")}
                onMessage={event => receive(event.nativeEvent.data)} style={{ flex: 1, backgroundColor: colors.cardBg }} />}
          </View> : <ScrollView contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingTop: spacing.md }} style={{ flexShrink: 1 }}>
            {content.links.map((link,index) => <Pressable key={link.id} testID="reference-directory-link" accessibilityRole="button" onPress={() => openTopic(link.id, link.title)}
              style={{ flexDirection: row, alignItems: "center", minHeight: 88, paddingVertical: spacing.lg, gap: spacing.md, borderTopWidth: index ? 1 : 0, borderTopColor: colors.border }}>
              <AppText weight="600" size={14} style={{ flex: 1, writingDirection: "ltr", textAlign: "left" }}>{link.title}</AppText>
              <AppText color={colors.accent} size={22}>{isFa ? "‹" : "›"}</AppText>
            </Pressable>)}
          </ScrollView>}
          <View style={{ flexDirection: row, alignItems: "center", marginTop: spacing.md, padding: spacing.lg, borderTopWidth: 1, borderTopColor: colors.border }}>
            <AppText muted size={12} style={{ flex: 1 }}>{isFa ? "منبع: UpToDate" : "Source: UpToDate"}</AppText>
            <Pressable accessibilityRole="button" accessibilityState={{ selected: favorite }} onPress={() => toggleFavorite({ source: "utd", id: article.id, title: article.title, section: article.section })} style={{ minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.md }}>
              <AppText color={colors.accent} weight="600" size={13}>{isFa ? favorite ? "ذخیره‌شده" : "ذخیره" : favorite ? "Saved" : "Save"}</AppText>
            </Pressable>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  </View>;
}
