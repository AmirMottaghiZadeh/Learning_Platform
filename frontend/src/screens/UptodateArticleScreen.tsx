import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { Modal, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { WebView } from "react-native-webview";

import { ChromeButton } from "@/components/ScreenChrome";
import { useBleedTop } from "@/components/AppShell";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { uptodateSource } from "@/offline/sources";
import { useNav } from "@/store/nav";
import { useReader } from "@/store/reader";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { NumberedOutlineNode, numberedOutline, outlineTops } from "@/utils/uptodateOutline";

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
function __utdEmitOp(payload) {
  var msg = JSON.stringify(Object.assign({ __utdOp: true }, payload));
  if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(msg);
  else if (window.parent && window.parent !== window) window.parent.postMessage(msg, "*");
}
function __utdGotoReference(num) {
  var ol = document.getElementById("reference");
  if (!ol || !num) return;
  var li = ol.children[parseInt(num, 10) - 1];
  if (!li) return;
  li.scrollIntoView({ block: "center" });
  li.classList.add("utd-ref-flash");
  setTimeout(function () { li.classList.remove("utd-ref-flash"); }, 1600);
}
// UpToDate's own markup links everything (cross-references, graphics,
// citations) through onclick="doOperation({...})" with no such function ever
// defined -- so none of those links did anything. This is that function.
// Section ids in body_html (H1, H23, ...) are sequential and say nothing
// about depth, so the level of each heading comes from the outline instead
// (same ids, parsed by parseOutline). The id may sit on the heading itself, on
// an empty anchor inside or just before it, or on a container wrapping the
// section, so the element whose text matches the outline title is the one
// that gets the level class.
function __utdNorm(s) { return (s || "").replace(/\\s+/g, " ").trim().toLowerCase(); }
function __utdHeadingFor(el, title) {
  var t = __utdNorm(title);
  if (!t) return null;
  function hit(node) { return !!node && node.nodeType === 1 && __utdNorm(node.textContent) === t; }
  function within(node) {
    if (!node || !node.querySelectorAll) return null;
    var all = node.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) if (hit(all[i])) return all[i];
    return null;
  }
  if (hit(el)) return el;
  if (hit(el.parentElement)) return el.parentElement;
  var inner = within(el);
  if (inner) return inner;
  var sib = el.nextElementSibling;
  if (hit(sib)) return sib;
  return within(sib);
}
// Each heading also gets its outline number ("3", "3.1", "3.1.2") as a
// leading span, styled per level in wrap()'s CSS.
function __utdMarkHeadings(levels, tops) {
  Object.keys(levels || {}).forEach(function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    var level = levels[id];
    var target = __utdHeadingFor(el, level.title);
    if (!target) return;
    target.classList.add("utd-l" + Math.min(3, level.depth + 1));
    if (level.num) {
      var num = document.createElement("span");
      num.className = "utd-num";
      num.textContent = level.num;
      target.insertBefore(num, target.firstChild);
    }
  });
  window.__utdTops = (tops || []).map(function (id) { return document.getElementById(id); });
}
// UpToDate's bullets are a <span class="glyph">●</span> leading a
// <p class="bulletIndentN">; those become the app's vertical-bar marker
// (numbered glyphs are left alone).
function __utdMarkBullets() {
  var glyphs = document.querySelectorAll(".glyph");
  for (var i = 0; i < glyphs.length; i++) {
    var g = glyphs[i];
    if (!/^[●•▪◦■–—-]$/.test((g.textContent || "").trim())) continue;
    g.classList.add("utd-bullet");
    if (g.parentElement) g.parentElement.classList.add("utd-li");
  }
}
// Reading position, for the progress bar and the home page's "continue
// from section N": how far down the article is scrolled, and which
// top-level section's heading was last passed.
window.__utdTops = [];
window.__utdLastReport = "";
function __utdReport() {
  var doc = document.scrollingElement || document.documentElement;
  var y = window.pageYOffset || doc.scrollTop || 0;
  var progress = Math.min(1, Math.max(0, y / Math.max(1, doc.scrollHeight - window.innerHeight)));
  var section = -1;
  for (var i = 0; i < window.__utdTops.length; i++) {
    var el = window.__utdTops[i];
    if (!el) continue;
    if (el.getBoundingClientRect().top <= 90) section = i;
    else break;
  }
  var key = Math.round(progress * 200) + ":" + section;
  if (key === window.__utdLastReport) return;
  window.__utdLastReport = key;
  __utdEmitOp({ type: "scroll", progress: progress, section: section });
}
var __utdPending = false;
window.addEventListener("scroll", function () {
  if (__utdPending) return;
  __utdPending = true;
  requestAnimationFrame(function () { __utdPending = false; __utdReport(); });
}, { passive: true });
window.doOperation = function (op) {
  if (!op) return;
  if (op.contentIds && op.contentIds.length) {
    __utdEmitOp({ type: "graphic", contentId: String(op.contentIds[0]) });
  } else if (op.contentId) {
    __utdEmitOp({ type: "nav", contentId: String(op.contentId), sectionName: op.sectionName || null });
  } else if (op.abstractNumbers && op.abstractNumbers.length) {
    __utdGotoReference(op.abstractNumbers[0]);
  } else if (op.sectionName) {
    __utdGoto(op.sectionName);
  }
};
true;
`;

type HeadingLevels = Record<string, { depth: number; title: string; num: string | null }>;

type WrapColors = {
  ink: string;
  prose: string;
  muted: string;
  bg: string;
  accent: string;
  accentSoft: string;
  onAccent: string;
  rule: string;
};

function headingLevels(nodes: NumberedOutlineNode[]): HeadingLevels {
  const levels: HeadingLevels = {};
  for (const node of nodes) levels[node.id] = { depth: node.depth, title: node.title, num: node.num };
  return levels;
}

function wrap(bodyHtml: string, c: WrapColors, levels: HeadingLevels = {}, tops: string[] = []) {
  const { ink, prose, muted, bg, accent, accentSoft, onAccent, rule } = c;
  // "<" escaped so a title can never close the script tag early.
  const levelsJson = JSON.stringify(levels).replace(/</g, "\\u003c");
  const topsJson = JSON.stringify(tops).replace(/</g, "\\u003c");
  // The article is UpToDate's own markup, which carries fixed widths, nested
  // tables and long unbroken strings. The page itself must never be wider
  // than the screen: everything is capped at the viewport, long words wrap,
  // and only a genuinely wide table/graphic scrolls sideways inside its own
  // box. minimum-scale=1 stops the WebView zooming out to fit overflow.
  return `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1">
<style>
  *, *::before, *::after { box-sizing:border-box; }
  html, body { max-width:100%; overflow-x:hidden; }
  body { font: 15px/1.7 -apple-system, "Segoe UI", Roboto, sans-serif; color:${prose};
         background:${bg}; margin:0; padding:18px 20px 110px; overflow-wrap:anywhere; word-break:break-word;
         -webkit-text-size-adjust:100%; }
  body *:not(td):not(th):not(tr):not(thead):not(tbody):not(tfoot):not(col):not(colgroup) {
    max-width:100%; }
  h1,h2,h3 { line-height:1.35; }
  a { color:${accent}; }
  pre, code { white-space:pre-wrap; }
  table { border-collapse:collapse; width:100%; display:block; overflow-x:auto; }
  table table { display:table; overflow-x:visible; }
  td,th { border:1px solid rgba(127,127,127,.3); padding:6px 8px; }
  img { max-width:100%; height:auto; }
  .utdGraphicWrapper, figure { overflow-x:auto; }
  mark.utd-hit { background:${accentSoft}; color:inherit; border-radius:2px; }
  mark.utd-hit-current { background:${accent}; color:#fff; }
  a.local, a.medical_review, a.graphic, a.abstract_t { cursor:pointer; }
  .utd-ref-flash { background:${accentSoft}; border-radius:2px; }
  #topicTitle { font-size:21px; font-weight:800; line-height:1.35; color:${ink}; margin:2px 0 10px; }
  #topicContributors, #topicContributors * { font-size:12px; line-height:1.5; color:${muted}; }
  #topicContributors dt { font-weight:700; margin-top:6px; }
  #topicContributors dd { margin:0; }
  /* Three numbered outline levels (design option B): a section's number in
     a filled badge, a subsection's in teal, anything deeper in grey over a
     dashed rule. A run-in heading's " — " is dropped once the heading sits
     on its own line. */
  .utd-l1, .utd-l2, .utd-l3 { display:block; line-height:1.35; color:${ink}; }
  .utd-l1 *, .utd-l2 *, .utd-l3 * { font-size:inherit; font-weight:inherit; }
  .utd-l1 + .headingEndMark, .utd-l2 + .headingEndMark, .utd-l3 + .headingEndMark { display:none; }
  .utd-l1 { display:flex; align-items:center; gap:12px; font-size:19px; font-weight:800; margin:32px 0 12px; }
  .utd-l1 .utd-num { flex:none; width:34px; height:34px; border-radius:10px; background:${accent};
                     color:${onAccent}; font-size:16px; display:flex; align-items:center; justify-content:center; }
  .utd-l2 { font-size:16.5px; font-weight:800; margin:24px 0 8px; }
  .utd-l2 .utd-num { color:${accent}; margin-right:8px; }
  .utd-l3 { font-size:15px; font-weight:700; color:${prose}; margin:18px 0 8px; padding-bottom:4px;
            border-bottom:1px dashed ${rule}; }
  .utd-l3 .utd-num { color:${muted}; margin-right:8px; }
  /* List marker (design option 6): a short vertical accent bar per bullet. */
  p.utd-li { position:relative; padding-left:18px; margin:6px 0; }
  p.bulletIndent2.utd-li { padding-left:36px; }
  p.bulletIndent3.utd-li { padding-left:54px; }
  .utd-bullet { position:absolute; left:2px; top:6px; width:3px; height:14px; border-radius:2px;
                background:${accent}; font-size:0; line-height:0; overflow:hidden; }
  .bulletIndent2 > .utd-bullet { left:20px; opacity:.55; }
  .bulletIndent3 > .utd-bullet { left:38px; opacity:.4; }
</style></head><body>${bodyHtml}<script>${FIND_SCRIPT}
__utdMarkHeadings(${levelsJson}, ${topsJson});
__utdMarkBullets();</script></body></html>`;
}

/** An UpToDate topic in the reader (design option 1). Keyed by article and
 * section, so a cross-reference into another topic -- the same screen with
 * new params -- starts fresh instead of keeping the last article's search,
 * position and loaded state. */
export function UptodateArticleScreen() {
  const id = String(useNav((s) => s.params.id ?? ""));
  const sectionId = useNav((s) => s.params.sectionId) as string | undefined;
  return <UptodateArticle key={`${id}|${sectionId ?? ""}`} />;
}

function UptodateArticle() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const bleedTop = useBleedTop(true);
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const id = String(useNav((s) => s.params.id ?? ""));
  const titleParam = String(useNav((s) => s.params.title ?? ""));
  const sectionId = useNav((s) => s.params.sectionId) as string | undefined;
  const openSearch = !!useNav((s) => s.params.openSearch);
  const rememberSection = useReader((s) => s.rememberSection);

  const [searchOpen, setSearchOpen] = useState(openSearch);
  const [query, setQuery] = useState("");
  const [find, setFind] = useState<FindResult>({ count: 0, current: 0 });
  const [graphicId, setGraphicId] = useState<string | null>(null);
  const [tocOpen, setTocOpen] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTop, setCurrentTop] = useState(-1);
  useBackInterceptor(graphicId !== null, () => setGraphicId(null));
  useBackInterceptor(tocOpen, () => setTocOpen(false));
  const debouncedQuery = useDebounced(query.trim(), 300);
  const webviewRef = useRef<WebView>(null);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const loadedOnce = useRef(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id],
    queryFn: () => uptodateSource.topic(id),
    enabled: !!id,
  });

  const outline = useMemo(() => numberedOutline(data?.outline_html ?? ""), [data]);
  const tops = useMemo(() => outlineTops(outline), [outline]);

  const wrapColors: WrapColors = {
    ink: colors.ink,
    prose: colors.proseInk,
    muted: colors.muted,
    bg: colors.cardBg,
    accent: colors.accent,
    accentSoft: `${colors.accent}33`,
    onAccent: colors.onAccent,
    rule: colors.trackBg,
  };
  const html = useMemo(
    () => (data ? wrap(data.body_html, wrapColors, headingLevels(outline), tops.map((top) => top.id)) : ""),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, outline, tops, colors],
  );

  // -- a table/figure/algorithm graphic opened from a reference link -------
  const {
    data: graphicTopic,
    isLoading: graphicLoading,
    isError: graphicTopicError,
  } = useQuery({
    queryKey: ["uptodate-topic", graphicId],
    queryFn: () => uptodateSource.topic(graphicId as string),
    enabled: !!graphicId,
  });

  const { data: graphicHtml, isError: graphicHtmlError } = useQuery({
    queryKey: ["uptodate-graphic-html", graphicId, graphicTopic?.body_html],
    queryFn: async () => {
      const raw = graphicTopic?.body_html ?? "";
      const imageIds = Array.from(
        new Set(Array.from(raw.matchAll(/<img[^>]*\ssrc="(\d+)"/g)).map((m) => m[1])),
      );
      if (!imageIds.length) return raw;
      const images = await Promise.all(
        imageIds.map((imageId) => uptodateSource.image(imageId).catch(() => null)),
      );
      let substituted = raw;
      imageIds.forEach((imageId, i) => {
        const image = images[i];
        if (image) {
          const dataUri = `data:${image.content_type};base64,${image.data_base64}`;
          substituted = substituted.split(`src="${imageId}"`).join(`src="${dataUri}"`);
        }
      });
      return substituted;
    },
    enabled: !!graphicTopic,
  });

  const graphicWrappedHtml = wrap(graphicHtml ?? "", wrapColors);

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

  const gotoSection = (target: string | undefined = sectionId) => {
    if (!target) return;
    if (Platform.OS === "web") {
      callWeb((win) => (win.__utdGoto as (s: string) => void)(target));
    } else {
      webviewRef.current?.injectJavaScript(`window.__utdGoto(${JSON.stringify(target)}); true;`);
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

  // doOperation() in the injected script can't return a value across the
  // WebView bridge (and even on web, the click happens inside the iframe's
  // own event loop), so every reference link reaches us as a posted message
  // tagged __utdOp rather than a function return value.
  const handleOp = (op: {
    type?: string;
    contentId?: string;
    sectionName?: string | null;
    progress?: number;
    section?: number;
  }) => {
    if (op.type === "scroll") {
      setProgress(op.progress ?? 0);
      const section = op.section ?? -1;
      setCurrentTop(section);
      if (section >= 0) rememberSection(`utd:${id}`, section);
    } else if (op.type === "nav" && op.contentId) {
      if (op.sectionName) {
        navigate("uptodateArticle", { id: op.contentId, sectionId: op.sectionName });
      } else {
        navigate("uptodateOutline", { id: op.contentId, title: "" });
      }
    } else if (op.type === "graphic" && op.contentId) {
      setGraphicId(op.contentId);
    }
  };

  const handleNativeMessage = (event: { nativeEvent: { data: string } }) => {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg && msg.__utdOp) {
        handleOp(msg);
        return;
      }
      setFind(msg as FindResult);
    } catch {
      /* ignore */
    }
  };

  const handleOpRef = useRef(handleOp);
  handleOpRef.current = handleOp;

  React.useEffect(() => {
    if (Platform.OS !== "web") return;
    const onMessage = (event: MessageEvent) => {
      if (event.source !== iframeRef.current?.contentWindow) return;
      try {
        const msg = JSON.parse(event.data as string);
        if (msg && msg.__utdOp) handleOpRef.current(msg);
      } catch {
        /* ignore */
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 16 + bleedTop, gap: 12 }}>
        <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
          <ChromeButton onPress={goBack} size={34}>
            <AppText weight="800" size={16} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <AppText weight="700" size={12} muted numberOfLines={1} style={{ flex: 1, textAlign: "left", writingDirection: "ltr" }}>
            {data?.title || titleParam}
          </AppText>
          <ChromeButton onPress={() => setTocOpen(true)} size={34}>
            <AppText weight="800" size={15} color={colors.ink}>
              ≡
            </AppText>
          </ChromeButton>
          <ChromeButton onPress={() => setSearchOpen((v) => !v)} size={34}>
            <AppText weight="800" size={15} color={searchOpen ? colors.accent : colors.ink}>
              ⌕
            </AppText>
          </ChromeButton>
        </View>
        <View style={{ height: 3, borderRadius: 2, backgroundColor: colors.trackBg, marginBottom: 2, overflow: "hidden" }}>
          <View style={{ width: `${Math.round(progress * 100)}%`, height: 3, borderRadius: 2, backgroundColor: colors.accent }} />
        </View>
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
              ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as object) : null),
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
            {t("articleLoadError")}
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

      <Modal visible={tocOpen} transparent animationType="fade" onRequestClose={() => setTocOpen(false)}>
        <Pressable
          style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.5)", justifyContent: "flex-end" }}
          onPress={() => setTocOpen(false)}
        >
          <Pressable
            onPress={() => undefined}
            style={{ maxHeight: "78%", backgroundColor: colors.cardBg, borderTopLeftRadius: 22, borderTopRightRadius: 22, paddingTop: 10 }}
          >
            <View style={{ alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: colors.trackBg, marginBottom: 10 }} />
            <AppText weight="900" size={15} style={{ paddingHorizontal: 20, marginBottom: 6 }}>
              {t("articleContents")}
            </AppText>
            <ScrollView contentContainerStyle={{ paddingHorizontal: 12, paddingBottom: 28 }}>
              {outline.map((node) => {
                const top = node.depth === 0;
                const on = top && tops[currentTop]?.id === node.id;
                return (
                  <Pressable
                    key={node.id}
                    onPress={() => {
                      setTocOpen(false);
                      gotoSection(node.id);
                    }}
                    style={{
                      paddingVertical: top ? 9 : 6,
                      paddingLeft: 8 + node.depth * 16,
                      paddingRight: 8,
                      borderRadius: 10,
                      backgroundColor: on ? `${colors.accent}14` : undefined,
                    }}
                  >
                    <AppText
                      weight={top ? "800" : "600"}
                      size={top ? 14 : 13}
                      color={top ? (on ? colors.accent : colors.ink) : node.depth > 1 ? colors.muted : colors.proseInk}
                      style={{ textAlign: "left", writingDirection: "ltr", lineHeight: top ? 21 : 19 }}
                    >
                      {node.num ? `${node.num}  ` : ""}
                      {node.title}
                    </AppText>
                  </Pressable>
                );
              })}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      <Modal
        visible={!!graphicId}
        transparent
        animationType="fade"
        onRequestClose={() => setGraphicId(null)}
      >
        <View style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.55)", padding: 16 }}>
          <View style={{ flex: 1, backgroundColor: colors.cardBg, borderRadius: 18, overflow: "hidden" }}>
            <View
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 10,
                paddingHorizontal: 16,
                paddingVertical: 12,
                borderBottomWidth: 1,
                borderBottomColor: colors.sheetLine,
              }}
            >
              <AppText weight="800" size={13} numberOfLines={2} style={{ flex: 1 }}>
                {graphicTopic?.title ?? ""}
              </AppText>
              <ChromeButton onPress={() => setGraphicId(null)} size={28}>
                <AppText weight="800" size={14} color={colors.ink}>
                  ×
                </AppText>
              </ChromeButton>
            </View>

            {graphicLoading || (!!graphicTopic && graphicHtml === undefined) ? (
              <LoadingState />
            ) : graphicTopicError || graphicHtmlError || !graphicTopic ? (
              <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
                <AppText muted weight="600">
                  {t("uptodateGraphicLoadError")}
                </AppText>
              </View>
            ) : Platform.OS === "web" ? (
              <iframe
                srcDoc={graphicWrappedHtml}
                style={{ flexGrow: 1, border: "none", width: "100%", height: "100%" }}
                title={graphicTopic.title}
              />
            ) : (
              <WebView
                originWhitelist={["*"]}
                source={{ html: graphicWrappedHtml }}
                style={{ flex: 1, backgroundColor: colors.cardBg }}
              />
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}
