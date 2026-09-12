import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { Platform, Pressable, TextInput, View } from "react-native";
import { WebView } from "react-native-webview";

import { uptodateApi } from "@/api/endpoints";
import { ChromeButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

type FindResult = { count: number; current: number };

// Shared by both the web <iframe> and the native <WebView>: wraps the raw
// UpToDate body HTML, then defines a tiny "find in page" scoped to just this
// article's text, plus a jump-to-heading helper for the outline screen.
// Every function also posts its result back via ReactNativeWebView when
// running inside the native WebView (harmless no-op on web, where the parent
// instead calls these functions directly and reads the return value, since a
// srcDoc iframe is same-origin and synchronously callable).
const FIND_SCRIPT = `
window.__utdMatches = [];
window.__utdIndex = -1;
function __utdPost(result) {
  if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(JSON.stringify(result));
  return result;
}
function __utdClear() {
  window.__utdMatches.forEach(function (m) {
    var parent = m.parentNode;
    if (!parent) return;
    parent.replaceChild(document.createTextNode(m.textContent), m);
    parent.normalize();
  });
  window.__utdMatches = [];
  window.__utdIndex = -1;
}
function __utdFocus() {
  window.__utdMatches.forEach(function (m, i) {
    m.className = i === window.__utdIndex ? "utd-hit utd-hit-current" : "utd-hit";
  });
  var el = window.__utdMatches[window.__utdIndex];
  if (el) el.scrollIntoView({ block: "center" });
}
function __utdSearch(term) {
  __utdClear();
  if (!term) return __utdPost({ count: 0, current: 0 });
  var root = document.getElementById("topicText") || document.body;
  var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
  var nodes = [];
  var n;
  while ((n = walker.nextNode())) nodes.push(n);
  var esc = term.replace(/[.*+?^\${}()|[\\]\\\\]/g, "\\\\$&");
  var re = new RegExp(esc, "gi");
  nodes.forEach(function (node) {
    var text = node.nodeValue;
    re.lastIndex = 0;
    if (!re.test(text)) return;
    re.lastIndex = 0;
    var frag = document.createDocumentFragment();
    var last = 0, m;
    while ((m = re.exec(text))) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      var mark = document.createElement("mark");
      mark.className = "utd-hit";
      mark.textContent = m[0];
      frag.appendChild(mark);
      window.__utdMatches.push(mark);
      last = m.index + m[0].length;
      if (m.index === re.lastIndex) re.lastIndex++;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(frag, node);
  });
  if (window.__utdMatches.length) {
    window.__utdIndex = 0;
    __utdFocus();
  }
  return __utdPost({ count: window.__utdMatches.length, current: window.__utdMatches.length ? 1 : 0 });
}
function __utdStep(delta) {
  if (!window.__utdMatches.length) return __utdPost({ count: 0, current: 0 });
  window.__utdIndex = (window.__utdIndex + delta + window.__utdMatches.length) % window.__utdMatches.length;
  __utdFocus();
  return __utdPost({ count: window.__utdMatches.length, current: window.__utdIndex + 1 });
}
function __utdGoto(sectionId) {
  if (!sectionId) return;
  var el = document.getElementById(sectionId);
  if (el) el.scrollIntoView({ block: "start" });
}
true;
`;

function wrap(bodyHtml: string, ink: string, bg: string, accent: string, accentSoft: string) {
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
  mark.utd-hit { background:${accentSoft}; color:inherit; border-radius:2px; }
  mark.utd-hit-current { background:${accent}; color:#fff; }
</style></head><body>${bodyHtml}<script>${FIND_SCRIPT}</script></body></html>`;
}

export function UptodateArticleScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const id = String(useNav((s) => s.params.id ?? ""));
  const titleParam = String(useNav((s) => s.params.title ?? ""));
  const sectionId = useNav((s) => s.params.sectionId) as string | undefined;

  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [find, setFind] = useState<FindResult>({ count: 0, current: 0 });
  const debouncedQuery = useDebounced(query.trim(), 300);
  const webviewRef = useRef<WebView>(null);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const loadedOnce = useRef(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id],
    queryFn: () => uptodateApi.topic(id),
    enabled: !!id,
  });

  const accentSoft = `${colors.accent}33`;
  const html = data
    ? wrap(data.body_html, colors.ink, colors.cardBg, colors.accent, accentSoft)
    : "";

  // -- cross-platform bridge to the injected find/goto script --------------
  // Web: a srcDoc iframe is same-origin, so the parent can call functions
  // defined in its global scope directly and read the return value. Native:
  // WebView.injectJavaScript() can't return a value, so the injected script
  // posts its result back via ReactNativeWebView.postMessage instead (see
  // FIND_SCRIPT's __utdPost and handleNativeMessage below).

  const callWeb = <T,>(fn: (win: Window & Record<string, unknown>) => T): T | undefined => {
    const win = iframeRef.current?.contentWindow as (Window & Record<string, unknown>) | null;
    if (!win) return undefined;
    try {
      return fn(win);
    } catch {
      return undefined;
    }
  };

  const search = (term: string) => {
    if (Platform.OS === "web") {
      const result = callWeb((win) => (win.__utdSearch as (t: string) => FindResult)(term));
      if (result) setFind(result);
    } else {
      webviewRef.current?.injectJavaScript(`window.__utdSearch(${JSON.stringify(term)}); true;`);
    }
  };

  const step = (delta: number) => {
    if (Platform.OS === "web") {
      const result = callWeb((win) => (win.__utdStep as (d: number) => FindResult)(delta));
      if (result) setFind(result);
    } else {
      webviewRef.current?.injectJavaScript(`window.__utdStep(${delta}); true;`);
    }
  };

  const gotoSection = () => {
    if (!sectionId) return;
    if (Platform.OS === "web") {
      callWeb((win) => (win.__utdGoto as (s: string) => void)(sectionId));
    } else {
      webviewRef.current?.injectJavaScript(`window.__utdGoto(${JSON.stringify(sectionId)}); true;`);
    }
  };

  React.useEffect(() => {
    search(debouncedQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQuery]);

  const handleWebLoad = () => {
    if (!loadedOnce.current) {
      loadedOnce.current = true;
      gotoSection();
    }
  };

  const handleNativeMessage = (event: { nativeEvent: { data: string } }) => {
    try {
      const result = JSON.parse(event.nativeEvent.data) as FindResult;
      setFind(result);
    } catch {
      /* ignore */
    }
  };

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
        <ChromeButton onPress={() => setSearchOpen((v) => !v)} size={30}>
          <AppText weight="800" size={14} color={searchOpen ? colors.accent : colors.ink}>
            ⌕
          </AppText>
        </ChromeButton>
      </View>

      {searchOpen ? (
        <View
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 8,
            paddingHorizontal: 18,
            paddingVertical: 10,
            borderBottomWidth: 1,
            borderBottomColor: colors.sheetLine,
            backgroundColor: colors.softBg,
          }}
        >
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={t("uptodateSearchInArticleHint")}
            placeholderTextColor={colors.muted}
            autoFocus
            style={{
              flex: 1,
              fontFamily: fontFamily("600"),
              fontSize: 13,
              color: colors.ink,
              textAlign: isFa ? "right" : "left",
              padding: 0,
            }}
          />
          {query.trim() ? (
            <AppText muted weight="700" size={12}>
              {find.count > 0
                ? `${n(find.current)} ${t("uptodateMatchCount")} ${n(find.count)}`
                : t("uptodateNoMatches")}
            </AppText>
          ) : null}
          <Pressable onPress={() => step(-1)} disabled={!find.count} hitSlop={8}>
            <AppText weight="800" size={16} color={find.count ? colors.ink : colors.muted}>
              {isFa ? "›" : "‹"}
            </AppText>
          </Pressable>
          <Pressable onPress={() => step(1)} disabled={!find.count} hitSlop={8}>
            <AppText weight="800" size={16} color={find.count ? colors.ink : colors.muted}>
              {isFa ? "‹" : "›"}
            </AppText>
          </Pressable>
        </View>
      ) : null}

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
          ref={iframeRef}
          srcDoc={html}
          onLoad={handleWebLoad}
          style={{ flexGrow: 1, border: "none", width: "100%", height: "100%" }}
          title={data.title}
        />
      ) : (
        <WebView
          ref={webviewRef}
          originWhitelist={["*"]}
          source={{ html }}
          onMessage={handleNativeMessage}
          injectedJavaScript={
            sectionId ? `window.__utdGoto(${JSON.stringify(sectionId)}); true;` : undefined
          }
          style={{ flex: 1, backgroundColor: colors.cardBg }}
        />
      )}
    </View>
  );
}
