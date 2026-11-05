import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { Modal, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { WebView } from "react-native-webview";
import { SafeAreaView } from "react-native-safe-area-context";

import { ChromeButton } from "@/components/ScreenChrome";
import { useBleedTop } from "@/components/AppShell";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { uptodateSource } from "@/offline/sources";
import { useNav } from "@/store/nav";
import { HIGHLIGHT_COLORS, HIGHLIGHT_PAINT, Highlight, useIsFavorite, useLibrary } from "@/store/library";
import { TEXT_SCALES, scaleStep, useReader } from "@/store/reader";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { stripHtml } from "@/utils/html";
import { TABLE_SCRIPT, tableLabels, tableStyles } from "@/utils/uptodateTables";
import {
  NumberedOutlineNode,
  RelatedGroup,
  RelatedItem,
  numberedOutline,
  outlineTops,
  parseRelated,
  relatedCount,
} from "@/utils/uptodateOutline";

type FindResult = { count: number; current: number };

// Shared by both the web <iframe> and the native <WebView>: wraps the raw
// UpToDate body HTML, then defines a tiny "find in page" scoped to just this
// article's text, plus a jump-to-heading helper for the outline screen.
// Every function also posts its result back via ReactNativeWebView when
// running inside the native WebView (harmless no-op on web, where the parent
// instead calls these functions directly and reads the return value, since a
// srcDoc iframe is same-origin and synchronously callable).
const FIND_SCRIPT = `
// Some imported references store italic markup as escaped text. Repair only
// known inline formatting in text nodes; never interpret attributes or alter
// links, scripts, tables, clinical comparison symbols or literal code blocks.
function __utdRepairInlineMarkup() {
  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
  var nodes = [], node;
  while ((node = walker.nextNode())) {
    var excluded = false;
    for (var parent = node.parentElement; parent; parent = parent.parentElement) {
      if (/^(SCRIPT|STYLE|CODE|PRE|TEXTAREA|NOSCRIPT)$/.test(parent.tagName)) { excluded = true; break; }
    }
    if (!excluded) nodes.push(node);
  }
  nodes.forEach(function (textNode) {
    var text = textNode.nodeValue.replace(/&(?:amp;)*lt;(\\/?(?:i|em|b|strong|sub|sup)\\s*)&(?:amp;)*gt;/gi, "<$1>");
    var token = /<(\\/?)(i|em|b|strong|sub|sup)\\s*>/gi;
    if (!token.test(text)) return;
    token.lastIndex = 0;
    var fragment = document.createDocumentFragment(), stack = [fragment], tags = [], last = 0, match;
    while ((match = token.exec(text))) {
      stack[stack.length - 1].appendChild(document.createTextNode(text.slice(last, match.index)));
      var tag = match[2].toLowerCase();
      if (match[1]) {
        var at = tags.lastIndexOf(tag);
        if (at >= 0) { tags.length = at; stack.length = at + 1; }
      } else {
        var element = document.createElement(tag);
        stack[stack.length - 1].appendChild(element);
        stack.push(element); tags.push(tag);
      }
      last = match.index + match[0].length;
    }
    stack[stack.length - 1].appendChild(document.createTextNode(text.slice(last)));
    textNode.parentNode.replaceChild(fragment, textNode);
  });
}
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
    // children moved out, not replaced by plain text: a highlight inside
    // a search hit must survive the search being cleared
    while (m.firstChild) parent.insertBefore(m.firstChild, m);
    parent.removeChild(m);
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
  while ((n = walker.nextNode())) if (!__utdSkipped(n)) nodes.push(n);
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
function __utdGotoSearchSection(sectionId) {
  if (!sectionId) return false;
  var nodes = document.querySelectorAll('[id]');
  var found = null;
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].id !== sectionId) continue;
    if (found) return false;
    found = nodes[i];
  }
  if (!found) return false;
  found.scrollIntoView({ block: "start" });
  return true;
}
function __utdGotoSearch(anchor) {
  if (!/^utd-[a-f0-9]{32}$/.test(anchor || "")) return false;
  var matches = document.querySelectorAll('[data-pharmenta-search-anchor="' + anchor + '"]');
  if (matches.length !== 1) return false;
  var el = matches[0];
  el.scrollIntoView({ block: "center" });
  el.classList.add("utd-search-flash");
  setTimeout(function () { el.classList.remove("utd-search-flash"); }, 2500);
  return true;
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
  requestAnimationFrame(function () { __utdPending = false; __utdReport(); __utdPlaceBar(); });
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
// Text size: every size in the page is in rem, so the root's font size
// scales the whole article; the reading position is kept.
function __utdSetScale(px) {
  var doc = document.scrollingElement || document.documentElement;
  var ratio = (window.pageYOffset || doc.scrollTop || 0) / Math.max(1, doc.scrollHeight);
  document.documentElement.style.fontSize = px + "px";
  window.scrollTo(0, ratio * doc.scrollHeight);
  __utdPlaceBar();
}
// "Related" (the outline's graphics, calculators and related topics): built
// by the app at the end of the page, moved to just before the references.
function __utdRelatedInit() {
  var rel = document.getElementById("utdRelated");
  if (!rel) return;
  var refs = document.getElementById("references");
  var root = document.getElementById("topicText");
  if (refs && refs.parentNode) refs.parentNode.insertBefore(rel, refs);
  else if (root) root.appendChild(rel);
  rel.style.display = "block";
  rel.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("[data-graphic],[data-topic]") : null;
    if (!a) return;
    e.preventDefault();
    var graphic = a.getAttribute("data-graphic"), topic = a.getAttribute("data-topic");
    if (graphic) __utdEmitOp({ type: "graphic", contentId: graphic });
    else if (topic) __utdEmitOp({ type: "nav", contentId: topic, sectionName: null });
  });
}
// Highlights. A highlight is a stretch of the article's text, counted in
// characters over the body's text nodes in order -- not the outline numbers
// the reader adds, nor "Related" or the colour bar -- so it lands on the same
// words each time the article opens. Each keeps a hash of its text: one whose
// article has been revised since is left unpainted.
window.__utdHls = [];
window.__utdHlOn = false;
window.__utdBarMode = null;
window.__utdBarDown = 0;
function __utdHlRoot() { return document.getElementById("topicText") || document.body; }
function __utdSkipped(node) {
  for (var el = node.parentNode; el && el.nodeType === 1; el = el.parentNode) {
    if (el.id === "utdRelated" || el.id === "utdHlBar") return true;
    if (el.tagName === "SCRIPT" || el.tagName === "STYLE") return true;
    if (el.hasAttribute && el.hasAttribute("data-utd-ui")) return true;
    if (el.classList && el.classList.contains("utd-num")) return true;
  }
  return false;
}
function __utdTexts() {
  var walker = document.createTreeWalker(__utdHlRoot(), NodeFilter.SHOW_TEXT, null, false);
  var list = [], at = 0, n;
  while ((n = walker.nextNode())) {
    if (__utdSkipped(n)) continue;
    list.push({ node: n, at: at });
    at += n.nodeValue.length;
  }
  return list;
}
function __utdFullText(list) {
  var parts = [];
  for (var i = 0; i < list.length; i++) parts.push(list[i].node.nodeValue);
  return parts.join("");
}
function __utdHash(text) {
  var h = 5381;
  for (var i = 0; i < text.length; i++) h = ((h * 33) ^ text.charCodeAt(i)) >>> 0;
  return h.toString(36);
}
function __utdOffset(list, container, offset) {
  if (container.nodeType === 3) {
    for (var i = 0; i < list.length; i++) if (list[i].node === container) return list[i].at + offset;
  }
  var point = document.createRange();
  try { point.setStart(container, offset); } catch (e) { return -1; }
  for (var j = 0; j < list.length; j++) if (point.comparePoint(list[j].node, 0) >= 0) return list[j].at;
  var last = list[list.length - 1];
  return last ? last.at + last.node.nodeValue.length : 0;
}
function __utdWrap(start, end, id, color) {
  var list = __utdTexts();
  for (var i = 0; i < list.length; i++) {
    var item = list[i], node = item.node, len = node.nodeValue.length;
    var a = Math.max(start, item.at), b = Math.min(end, item.at + len);
    if (a >= b) continue;
    // whitespace between table cells or list items is left alone
    if (!node.nodeValue.slice(a - item.at, b - item.at).trim()) continue;
    if (b - item.at < len) node.splitText(b - item.at);
    var target = a - item.at > 0 ? node.splitText(a - item.at) : node;
    var mark = document.createElement("mark");
    mark.className = "utd-hl utd-hl-" + color;
    mark.setAttribute("data-hl", id);
    target.parentNode.insertBefore(mark, target);
    mark.appendChild(target);
  }
}
function __utdUnwrap(id) {
  var marks = document.querySelectorAll('mark.utd-hl[data-hl="' + id + '"]');
  for (var i = 0; i < marks.length; i++) {
    var m = marks[i], parent = m.parentNode;
    if (!parent) continue;
    while (m.firstChild) parent.insertBefore(m.firstChild, m);
    parent.removeChild(m);
    parent.normalize();
  }
}
function __utdHlSave() { __utdEmitOp({ type: "highlights", items: window.__utdHls }); }
function __utdHlAdd(range, color) {
  var list = __utdTexts();
  var start = __utdOffset(list, range.startContainer, range.startOffset);
  var end = __utdOffset(list, range.endContainer, range.endOffset);
  if (start < 0 || end <= start) return;
  var text = __utdFullText(list).slice(start, end);
  if (!text.trim()) return;
  // a new highlight replaces those it overlaps
  window.__utdHls = window.__utdHls.filter(function (h) {
    if (h.start < end && h.end > start) { __utdUnwrap(h.id); return false; }
    return true;
  });
  var id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  __utdWrap(start, end, id, color);
  window.__utdHls.push({ id: id, start: start, end: end, color: color, check: __utdHash(text) });
  __utdHlSave();
}
function __utdHlRecolor(id, color) {
  var marks = document.querySelectorAll('mark.utd-hl[data-hl="' + id + '"]');
  for (var i = 0; i < marks.length; i++) marks[i].className = "utd-hl utd-hl-" + color;
  window.__utdHls.forEach(function (h) { if (h.id === id) h.color = color; });
  __utdHlSave();
}
function __utdHlRemove(id) {
  __utdUnwrap(id);
  window.__utdHls = window.__utdHls.filter(function (h) { return h.id !== id; });
  __utdHlSave();
}
// The highlights a selection overlaps: selecting over a highlight is also
// how one on a link (where a tap follows the link) is removed.
function __utdOverlapped(range) {
  var list = __utdTexts();
  var start = __utdOffset(list, range.startContainer, range.startOffset);
  var end = __utdOffset(list, range.endContainer, range.endOffset);
  return window.__utdHls.filter(function (h) { return h.start < end && h.end > start; });
}
function __utdHlRemoveIn(range) {
  var gone = __utdOverlapped(range);
  if (!gone.length) return;
  gone.forEach(function (h) { __utdUnwrap(h.id); });
  window.__utdHls = window.__utdHls.filter(function (h) { return gone.indexOf(h) < 0; });
  __utdHlSave();
}
function __utdBar() {
  var bar = document.getElementById("utdHlBar");
  if (bar) return bar;
  bar = document.createElement("div");
  bar.id = "utdHlBar";
  (window.__utdHlColors || []).forEach(function (c) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "utd-hl-dot utd-hl-" + c;
    b.setAttribute("data-color", c);
    b.setAttribute("aria-label", c);
    bar.appendChild(b);
  });
  var del = document.createElement("button");
  del.type = "button";
  del.className = "utd-hl-del";
  del.setAttribute("data-del", "1");
  del.setAttribute("aria-label", "remove");
  del.textContent = "\u2715";
  bar.appendChild(del);
  // a press on the bar keeps the selection (desktop) and is not taken for
  // the selection ending (phones collapse it before the tap lands)
  bar.addEventListener("mousedown", function (e) { window.__utdBarDown = Date.now(); e.preventDefault(); });
  bar.addEventListener("touchstart", function () { window.__utdBarDown = Date.now(); }, { passive: true });
  bar.addEventListener("click", function (e) {
    var t = e.target, mode = window.__utdBarMode;
    if (!t || !t.getAttribute || !mode) return;
    var color = t.getAttribute("data-color");
    if (color && mode.kind === "new") __utdHlAdd(mode.range, color);
    else if (color && mode.kind === "edit") __utdHlRecolor(mode.id, color);
    else if (t.getAttribute("data-del") && mode.kind === "edit") __utdHlRemove(mode.id);
    else if (t.getAttribute("data-del") && mode.kind === "new") __utdHlRemoveIn(mode.range);
    else return;
    var sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    __utdHideBar();
  });
  document.body.appendChild(bar);
  return bar;
}
function __utdBarRect() {
  var mode = window.__utdBarMode;
  if (!mode) return null;
  if (mode.kind === "new") return mode.range.getBoundingClientRect();
  var mark = document.querySelector('mark.utd-hl[data-hl="' + mode.id + '"]');
  return mark ? mark.getBoundingClientRect() : null;
}
function __utdPlaceBar() {
  var bar = document.getElementById("utdHlBar");
  var rect = __utdBarRect();
  if (!bar || !rect || bar.style.display !== "flex") return;
  var w = bar.offsetWidth, h = bar.offsetHeight;
  var x = Math.max(8, Math.min(window.innerWidth - w - 8, rect.left + rect.width / 2 - w / 2));
  // Android shows its own copy/share menu above a selection: ours goes below
  var below = rect.bottom + 14, above = rect.top - h - 14;
  var y = below + h < window.innerHeight - 8 ? below : Math.max(8, above);
  bar.style.left = x + "px";
  bar.style.top = y + "px";
}
function __utdShowBar(mode) {
  var bar = __utdBar();
  window.__utdBarMode = mode;
  // the remove button: for a tapped highlight, or a selection over one
  bar.className = mode.kind === "edit" || (mode.kind === "new" && __utdOverlapped(mode.range).length) ? "edit" : "";
  bar.style.display = "flex";
  __utdPlaceBar();
}
function __utdHideBar() {
  var bar = document.getElementById("utdHlBar");
  if (bar) bar.style.display = "none";
  window.__utdBarMode = null;
}
var __utdSelTimer = null;
function __utdOnSelection() {
  var sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
    var mode = window.__utdBarMode;
    if (mode && mode.kind === "new" && Date.now() - window.__utdBarDown > 800) __utdHideBar();
    return;
  }
  var range = sel.getRangeAt(0);
  var inside = range.commonAncestorContainer;
  var rel = document.getElementById("utdRelated");
  if (!__utdHlRoot().contains(inside) || (rel && rel.contains(inside))) return;
  if (!range.toString().trim()) return;
  __utdShowBar({ kind: "new", range: range.cloneRange() });
}
document.addEventListener("selectionchange", function () {
  if (!window.__utdHlOn) return;
  clearTimeout(__utdSelTimer);
  __utdSelTimer = setTimeout(__utdOnSelection, 250);
});
document.addEventListener("click", function (e) {
  if (!window.__utdHlOn) return;
  var t = e.target, bar = document.getElementById("utdHlBar");
  if (bar && bar.contains(t)) return;
  var mark = t && t.closest ? t.closest("mark.utd-hl") : null;
  var sel = window.getSelection();
  if (mark && (!sel || sel.isCollapsed)) __utdShowBar({ kind: "edit", id: mark.getAttribute("data-hl") });
  else if (window.__utdBarMode && window.__utdBarMode.kind === "edit") __utdHideBar();
});
function __utdHighlightsInit(items, colors) {
  window.__utdHlOn = true;
  window.__utdHlColors = colors;
  window.__utdHls = (items || []).slice();
  var full = __utdFullText(__utdTexts());
  window.__utdHls
    .slice()
    .sort(function (a, b) { return a.start - b.start; })
    .forEach(function (h) {
      if (h.end <= full.length && __utdHash(full.slice(h.start, h.end)) === h.check) __utdWrap(h.start, h.end, h.id, h.color);
    });
}
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

/** The article's normal text size, in px; the reader's size scales it. */
const BASE_TEXT_PX = 15;

const escapeHtml = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** "Related" at the end of the article: the outline's graphics (grouped as
 * UpToDate groups them), calculators and related topics. English, like the
 * article. Its links are handled by __utdRelatedInit. */
function relatedHtml(groups: RelatedGroup[]): string {
  if (!groups.length) return "";
  const item = (it: RelatedItem) => {
    const attr = "graphic" in it.target ? `data-graphic="${it.target.graphic}"` : `data-topic="${it.target.topic}"`;
    const kind = "graphic" in it.target ? "g" : "t";
    return `<a class="utd-rel-item utd-rel-${kind}" ${attr} href="#">${escapeHtml(it.title)}</a>`;
  };
  const block = (title: string, parts: RelatedGroup[]) => {
    const count = parts.reduce((sum, g) => sum + g.items.length, 0);
    const lists = parts
      .map((g) => `${g.heading ? `<div class="utd-rel-sub">${escapeHtml(g.heading)} <span>${g.items.length}</span></div>` : ""}<div class="utd-rel-list">${g.items.map(item).join("")}</div>`)
      .join("");
    return `<section class="utd-rel-block"><h3>${title} <span>${count}</span></h3>${lists}</section>`;
  };
  const of = (kind: RelatedGroup["kind"]) => groups.filter((g) => g.kind === kind);
  const blocks = [
    of("graphics").length ? block("Graphics", of("graphics")) : "",
    of("calculators").length ? block("Calculators", of("calculators")) : "",
    of("topics").length ? block("Related topics", of("topics")) : "",
  ].join("");
  return `<div id="utdRelated" style="display:none"><div class="utd-rel-title">RELATED</div>${blocks}</div>`;
}

type WrapOptions = {
  levels?: HeadingLevels;
  tops?: string[];
  /** text size, as a share of BASE_TEXT_PX */
  scale?: number;
  related?: RelatedGroup[];
  /** the article's saved highlights; null when the page takes none (a graphic) */
  highlights?: Highlight[] | null;
  dark?: boolean;
  isFa?: boolean;
  tableContext?: "article" | "graphic";
  tableViewer?: { index: number; title: string };
};

function wrap(bodyHtml: string, c: WrapColors, opts: WrapOptions = {}) {
  const { ink, prose, muted, bg, accent, accentSoft, onAccent, rule } = c;
  const { levels = {}, tops = [], scale = 1, related = [], highlights = null, dark = false } = opts;
  // "<" escaped so a title can never close the script tag early.
  const json = (value: unknown) => JSON.stringify(value).replace(/</g, "\\u003c");
  const paint = HIGHLIGHT_COLORS.map((color) => `.utd-hl-${color} { background:${HIGHLIGHT_PAINT[color][dark ? 1 : 0]}; }`).join("\n  ");
  // The article is UpToDate's own markup, which carries fixed widths, nested
  // tables and long unbroken strings. The page itself must never be wider
  // than the screen: everything is capped at the viewport, long words wrap,
  // and only a genuinely wide table/graphic scrolls sideways inside its own
  // box. minimum-scale=1 stops the WebView zooming out to fit overflow.
  // Every size is in rem, so the root's font size (the reader's text size)
  // scales the whole page.
  return `<!doctype html><html style="font-size:${(BASE_TEXT_PX * scale).toFixed(2)}px"><head><meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1">
<style>
  *, *::before, *::after { box-sizing:border-box; }
  html, body { max-width:100%; overflow-x:hidden; }
  body { font-size:1rem; line-height:1.7; font-family:-apple-system, "Segoe UI", Roboto, sans-serif; color:${prose};
         background:${bg}; margin:0; padding:18px 20px 110px; overflow-wrap:anywhere; word-break:break-word;
         -webkit-text-size-adjust:100%; }
  body *:not(td):not(th):not(tr):not(thead):not(tbody):not(tfoot):not(col):not(colgroup) {
    max-width:100%; }
  ::selection { background:${accentSoft}; }
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
  mark.utd-hl { color:inherit; border-radius:2px; padding:0 1px; }
  ${paint}
  #utdHlBar { position:fixed; z-index:50; display:none; align-items:center; gap:10px; padding:8px 12px;
              background:${dark ? "#26302D" : "#14201D"}; border-radius:999px; box-shadow:0 6px 20px rgba(0,0,0,.28); }
  #utdHlBar button { border:0; padding:0; margin:0; cursor:pointer; -webkit-tap-highlight-color:transparent; }
  #utdHlBar .utd-hl-dot { width:30px; height:30px; border-radius:50%; border:2px solid rgba(255,255,255,.85); }
  #utdHlBar .utd-hl-del { width:30px; height:30px; border-radius:50%; background:rgba(255,255,255,.14);
                          color:#fff; font-size:15px; line-height:30px; display:none; }
  #utdHlBar.edit .utd-hl-del { display:block; }
  a.local, a.medical_review, a.graphic, a.abstract_t { cursor:pointer; }
  .utd-ref-flash { background:${accentSoft}; border-radius:2px; }
  #topicTitle { font-size:1.4rem; font-weight:800; line-height:1.35; color:${ink}; margin:2px 0 10px; }
  #topicContributors, #topicContributors * { font-size:0.8rem; line-height:1.5; color:${muted}; }
  #topicContributors dt { font-weight:700; margin-top:6px; }
  #topicContributors dd { margin:0; }
  /* Three numbered outline levels (design option B): a section's number in
     a filled badge, a subsection's in teal, anything deeper in grey over a
     dashed rule. A run-in heading's " — " is dropped once the heading sits
     on its own line. */
  .utd-l1, .utd-l2, .utd-l3 { display:block; line-height:1.35; color:${ink}; }
  .utd-l1 *, .utd-l2 *, .utd-l3 * { font-size:inherit; font-weight:inherit; }
  .utd-l1 + .headingEndMark, .utd-l2 + .headingEndMark, .utd-l3 + .headingEndMark { display:none; }
  .utd-l1 { display:flex; align-items:center; gap:12px; font-size:1.27rem; font-weight:800; margin:32px 0 12px; }
  .utd-l1 .utd-num { flex:none; width:2.27rem; height:2.27rem; border-radius:10px; background:${accent};
                     color:${onAccent}; font-size:1.07rem; display:flex; align-items:center; justify-content:center; }
  .utd-l2 { font-size:1.1rem; font-weight:800; margin:24px 0 8px; }
  .utd-l2 .utd-num { color:${accent}; margin-right:8px; }
  .utd-l3 { font-size:1rem; font-weight:700; color:${prose}; margin:18px 0 8px; padding-bottom:4px;
            border-bottom:1px dashed ${rule}; }
  .utd-l3 .utd-num { color:${muted}; margin-right:8px; }
  /* List marker (design option 6): a short vertical accent bar per bullet. */
  p.utd-li { position:relative; padding-left:18px; margin:6px 0; }
  p.bulletIndent2.utd-li { padding-left:36px; }
  p.bulletIndent3.utd-li { padding-left:54px; }
  .utd-bullet { position:absolute; left:2px; top:0.4rem; width:3px; height:0.93rem; border-radius:2px;
                background:${accent}; font-size:0; line-height:0; overflow:hidden; }
  .bulletIndent2 > .utd-bullet { left:20px; opacity:.55; }
  .bulletIndent3 > .utd-bullet { left:38px; opacity:.4; }
  .utd-search-flash { outline: 3px solid ${accent}; background: ${accentSoft}; }
  /* "Related": the outline's graphics, calculators and related topics. */
  #utdRelated { margin:36px 0 28px; padding-top:18px; border-top:2px solid ${accent}; }
  .utd-rel-title { font-size:0.8rem; font-weight:800; letter-spacing:.12em; color:${accent}; margin-bottom:6px; }
  .utd-rel-block { margin:14px 0 18px; }
  .utd-rel-block h3 { font-size:1.07rem; font-weight:800; color:${ink}; margin:0 0 8px; }
  .utd-rel-block h3 span, .utd-rel-sub span { color:${muted}; font-weight:700; font-size:0.85em; }
  .utd-rel-sub { font-size:0.87rem; font-weight:800; color:${prose}; margin:12px 0 4px; text-transform:uppercase; letter-spacing:.04em; }
  .utd-rel-list { border:1px solid ${rule}; border-radius:12px; overflow:hidden; }
  a.utd-rel-item { display:flex; align-items:center; gap:10px; padding:10px 12px; color:${ink}; text-decoration:none;
                   font-size:0.93rem; line-height:1.45; border-top:1px solid ${rule}; }
  a.utd-rel-item:first-child { border-top:0; }
  a.utd-rel-item::before { content:""; flex:none; width:8px; height:8px; border-radius:2px; background:${accent}; }
  a.utd-rel-t::before { border-radius:50%; background:transparent; border:2px solid ${accent}; }
  a.utd-rel-item::after { content:"›"; margin-left:auto; padding-left:8px; color:${muted}; font-size:1.1rem; }
  ${tableStyles(c, dark)}
</style></head><body>${bodyHtml}${relatedHtml(related)}<script>${FIND_SCRIPT}
${TABLE_SCRIPT}
__utdRepairInlineMarkup();
__utdTablesInit(${json({ labels: tableLabels(!!opts.isFa), context: opts.tableContext ?? "article", viewer: opts.tableViewer })});
__utdMarkHeadings(${json(levels)}, ${json(tops)});
__utdMarkBullets();
__utdRelatedInit();
${highlights ? `__utdHighlightsInit(${json(highlights)}, ${json(HIGHLIGHT_COLORS)});` : ""}</script></body></html>`;
}

/** An UpToDate topic in the reader (design option 1). Keyed by article and
 * section, so a cross-reference into another topic -- the same screen with
 * new params -- starts fresh instead of keeping the last article's search,
 * position and loaded state. */
export function UptodateArticleScreen() {
  const id = String(useNav((s) => s.params.id ?? ""));
  const sectionId = useNav((s) => s.params.sectionId) as string | undefined;
  const searchAnchor = useNav((s) => s.params.searchAnchor) as string | undefined;
  const searchContentHash = useNav((s) => s.params.searchContentHash) as string | undefined;
  return <UptodateArticle key={`${id}|${sectionId ?? ""}|${searchAnchor ?? ""}|${searchContentHash ?? ""}`} />;
}

function UptodateArticle() {
  const { t, isFa, n, row } = useLang();
  const { colors, isDark } = useTheme();
  const bleedTop = useBleedTop(true);
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const id = String(useNav((s) => s.params.id ?? ""));
  const articleKey = `utd:${id}`;
  const titleParam = String(useNav((s) => s.params.title ?? ""));
  const sectionId = useNav((s) => s.params.sectionId) as string | undefined;
  const rawAnchor = useNav((s) => s.params.searchAnchor) as string | undefined;
  const rawHash = useNav((s) => s.params.searchContentHash) as string | undefined;
  const searchAnchor = typeof rawAnchor === "string" && /^utd-[a-f0-9]{32}$/.test(rawAnchor) ? rawAnchor : undefined;
  const searchContentHash = typeof rawHash === "string" && /^[a-f0-9]{64}$/.test(rawHash) ? rawHash : undefined;
  const searchRequested = rawAnchor !== undefined || rawHash !== undefined;
  const searchTarget = !!(searchAnchor && searchContentHash);
  const openSearch = !!useNav((s) => s.params.openSearch);
  const rememberSection = useReader((s) => s.rememberSection);
  const textScale = useReader((s) => s.textScale) || 1;
  const setTextScale = useReader((s) => s.setTextScale);
  const setHighlights = useLibrary((s) => s.setHighlights);
  const toggleFavorite = useLibrary((s) => s.toggleFavorite);
  const favorite = useIsFavorite("utd", id);
  // Read once per page build: a change made in the page is already shown
  // there, so it must not rebuild (and reload) the page.
  const scaleRef = useRef(textScale);
  scaleRef.current = textScale;
  const highlightsRef = useRef<Highlight[]>(useLibrary.getState().highlights[articleKey] ?? []);

  const [searchOpen, setSearchOpen] = useState(openSearch);
  const [query, setQuery] = useState("");
  const [find, setFind] = useState<FindResult>({ count: 0, current: 0 });
  const [graphicId, setGraphicId] = useState<string | null>(null);
  const [tableView, setTableView] = useState<{ html: string; index: number; title: string } | null>(null);
  const closeAuxiliary = () => tableView ? setTableView(null) : setGraphicId(null);
  const [tocOpen, setTocOpen] = useState(false);
  const [textOpen, setTextOpen] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTop, setCurrentTop] = useState(-1);
  useBackInterceptor(graphicId !== null || tableView !== null, closeAuxiliary);
  useBackInterceptor(tocOpen, () => setTocOpen(false));
  useBackInterceptor(textOpen, () => setTextOpen(false));
  const debouncedQuery = useDebounced(query.trim(), 300);
  const webviewRef = useRef<WebView>(null);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const auxiliaryIframeRef = useRef<HTMLIFrameElement | null>(null);
  const loadedOnce = useRef(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["uptodate-topic", id, searchAnchor, searchContentHash],
    queryFn: () => searchTarget
      ? uptodateSource.topicAtAnchor(id, searchContentHash!, searchAnchor!)
      : uptodateSource.topic(id),
    enabled: !!id,
  });

  const outline = useMemo(() => numberedOutline(data?.outline_html ?? ""), [data]);
  const tops = useMemo(() => outlineTops(outline), [outline]);
  const related = useMemo(() => parseRelated(data?.outline_html ?? ""), [data]);

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
    () =>
      data
        ? wrap(data.body_html, wrapColors, {
            levels: headingLevels(outline),
            tops: tops.map((top) => top.id),
            scale: scaleRef.current,
            related,
            highlights: highlightsRef.current,
            dark: isDark,
            isFa,
          })
        : "",
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, outline, tops, related, colors, isFa],
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

  const auxiliaryHtml = useMemo(() => wrap(tableView?.html ?? graphicHtml ?? "", wrapColors, {
    scale: textScale, dark: isDark, isFa, tableContext: "graphic",
    tableViewer: tableView ? { index: tableView.index, title: tableView.title } : undefined,
  }), [tableView, graphicHtml, colors, textScale, isDark, isFa]);

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

  const applyScale = (scale: number) => {
    const px = (BASE_TEXT_PX * scale).toFixed(2);
    if (Platform.OS === "web") callWeb((win) => (win.__utdSetScale as (v: string) => void)(px));
    else webviewRef.current?.injectJavaScript(`window.__utdSetScale(${JSON.stringify(px)}); true;`);
  };

  const changeScale = (step: number) => {
    const next = TEXT_SCALES[Math.min(TEXT_SCALES.length - 1, Math.max(0, step))];
    setTextScale(next);
    applyScale(next);
  };

  const gotoSection = (target: string | undefined = sectionId) => {
    if (!target) return;
    if (Platform.OS === "web") {
      callWeb((win) => (win.__utdGoto as (s: string) => void)(target));
    } else {
      webviewRef.current?.injectJavaScript(`window.__utdGoto(${JSON.stringify(target)}); true;`);
    }
  };

  const searchJump = data?.search_anchor_status === "matched" && searchAnchor
    ? `if (!window.__utdGotoSearch(${JSON.stringify(searchAnchor)})) window.__utdGotoSearchSection(${JSON.stringify(sectionId ?? "")}); true;`
    : data?.search_anchor_status === "missing" && sectionId
      ? `window.__utdGotoSearchSection(${JSON.stringify(sectionId)}); true;`
      : undefined;

  React.useEffect(() => {
    search(debouncedQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQuery]);

  const handleWebLoad = () => {
    if (!loadedOnce.current) {
      loadedOnce.current = true;
      if (searchRequested) {
        if (data?.search_anchor_status === "matched" && searchAnchor) {
          const found = callWeb((win) => (win.__utdGotoSearch as (s: string) => boolean)(searchAnchor));
          if (!found && sectionId) callWeb((win) => (win.__utdGotoSearchSection as (s: string) => boolean)(sectionId));
        } else if (data?.search_anchor_status === "missing") {
          if (sectionId) callWeb((win) => (win.__utdGotoSearchSection as (s: string) => boolean)(sectionId));
        }
      } else {
        gotoSection();
      }
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
    items?: Highlight[];
    index?: number;
    context?: string;
    title?: string;
  }) => {
    if (op.type === "table" && Number.isInteger(op.index) && op.index! >= 0) {
      const source = op.context === "article" ? data?.body_html : op.context === "graphic" ? graphicHtml : undefined;
      const title = stripHtml((typeof op.title === "string" && op.title.trim()
        ? op.title.slice(0, 500)
        : (op.context === "graphic" ? graphicTopic?.title : data?.title)) || titleParam);
      if (source) setTableView({ html: source, index: op.index!, title });
    } else if (op.type === "table-close") {
      setTableView(null);
    } else if (op.type === "highlights" && Array.isArray(op.items)) {
      const items = op.items.filter(
        (h) => h && typeof h.id === "string" && Number.isFinite(h.start) && Number.isFinite(h.end)
          && (HIGHLIGHT_COLORS as readonly string[]).includes(h.color),
      );
      highlightsRef.current = items;
      setHighlights(articleKey, items);
    } else if (op.type === "scroll") {
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

  const handleAuxiliaryMessage = (event: { nativeEvent: { data: string } }) => {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg?.__utdOp && (msg.type === "table" || msg.type === "table-close")) handleOpRef.current(msg);
    } catch { /* Ignore messages outside the table controls. */ }
  };

  React.useEffect(() => {
    if (Platform.OS !== "web") return;
    const onMessage = (event: MessageEvent) => {
      const main = event.source === iframeRef.current?.contentWindow;
      const auxiliary = event.source === auxiliaryIframeRef.current?.contentWindow;
      if (!main && !auxiliary) return;
      try {
        const msg = JSON.parse(event.data as string);
        if (msg?.__utdOp && (main || msg.type === "table" || msg.type === "table-close")) handleOpRef.current(msg);
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
        <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
          <ChromeButton onPress={goBack} size={34}>
            <AppText weight="800" size={16} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <AppText weight="700" size={12} muted numberOfLines={1} style={{ flex: 1, textAlign: "left", writingDirection: "ltr" }}>
            {stripHtml(data?.title || titleParam)}
          </AppText>
          <ChromeButton
            onPress={() =>
              toggleFavorite({ source: "utd", id, title: stripHtml(data?.title || titleParam), section: data?.section ?? "" })
            }
            size={34}
            accessibilityLabel={t(favorite ? "favoriteRemove" : "favoriteAdd")}
          >
            <AppText weight="800" size={16} color={favorite ? "#E0A526" : colors.ink}>
              {favorite ? "★" : "☆"}
            </AppText>
          </ChromeButton>
          <ChromeButton onPress={() => setTextOpen(true)} size={34} accessibilityLabel={t("readerTextSize")}>
            <AppText weight="800" size={13} color={textOpen ? colors.accent : colors.ink}>
              Aa
            </AppText>
          </ChromeButton>
          <ChromeButton onPress={() => setTocOpen(true)} size={34} accessibilityLabel={t("articleContents")}>
            <AppText weight="800" size={15} color={colors.ink}>
              ≡
            </AppText>
          </ChromeButton>
          <ChromeButton onPress={() => setSearchOpen((v) => !v)} size={34} accessibilityLabel={t("uptodateSearchInArticleHint")}>
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
            paddingHorizontal: 14,
            paddingVertical: 8,
            borderBottomWidth: 1,
            borderBottomColor: colors.sheetLine,
            backgroundColor: colors.softBg,
          }}
        >
          <View
            style={{
              flex: 1,
              flexDirection: row,
              alignItems: "center",
              gap: 8,
              height: 44,
              paddingHorizontal: 12,
              borderRadius: 12,
              backgroundColor: colors.inputBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
            }}
          >
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder={t("uptodateSearchInArticleHint")}
              placeholderTextColor={colors.muted}
              autoFocus
              returnKeyType="search"
              onSubmitEditing={() => step(1)}
              style={{
                flex: 1,
                minWidth: 0,
                fontFamily: fontFamily("600"),
                fontSize: 14,
                color: colors.ink,
                textAlign: query ? "left" : isFa ? "right" : "left",
                writingDirection: query ? "ltr" : undefined,
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
          </View>
          {/* up = the match before, down = the match after: the article runs
              top to bottom whatever the app's language */}
          <FindStepButton glyph="▲" label={t("findPrevious")} disabled={!find.count} onPress={() => step(-1)} />
          <FindStepButton glyph="▼" label={t("findNext")} disabled={!find.count} onPress={() => step(1)} />
          <FindStepButton
            glyph="✕"
            label={t("dismiss")}
            onPress={() => {
              setQuery("");
              setSearchOpen(false);
            }}
          />
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
            searchRequested ? searchJump : sectionId ? `window.__utdGoto(${JSON.stringify(sectionId)}); true;` : undefined
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
              {related.length ? (
                <Pressable
                  onPress={() => {
                    setTocOpen(false);
                    gotoSection("utdRelated");
                  }}
                  style={{ marginTop: 6, paddingVertical: 10, paddingHorizontal: 8, borderRadius: 10, borderTopWidth: 1, borderTopColor: colors.sheetLine }}
                >
                  <AppText weight="800" size={14} color={colors.accent} style={{ textAlign: "left", writingDirection: "ltr" }}>
                    {`Related · ${relatedCount(related)}`}
                  </AppText>
                  <AppText weight="600" size={12} muted style={{ textAlign: "left", writingDirection: "ltr", marginTop: 2 }}>
                    {relatedSummary(related)}
                  </AppText>
                </Pressable>
              ) : null}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      <Modal visible={textOpen} transparent animationType="fade" onRequestClose={() => setTextOpen(false)}>
        <Pressable
          style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.4)", justifyContent: "flex-end" }}
          onPress={() => setTextOpen(false)}
        >
          <Pressable
            onPress={() => undefined}
            style={{ backgroundColor: colors.cardBg, borderTopLeftRadius: 22, borderTopRightRadius: 22, padding: 20, paddingTop: 10, gap: 16 }}
          >
            <View style={{ alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: colors.trackBg }} />
            <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
              <AppText weight="900" size={15}>
                {t("readerTextSize")}
              </AppText>
              <AppText weight="800" size={13} color={colors.accent}>
                {`${n(Math.round(textScale * 100))}${isFa ? "٪" : "%"}`}
              </AppText>
            </View>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
              <TextSizeButton small disabled={scaleStep(textScale) === 0} onPress={() => changeScale(scaleStep(textScale) - 1)} />
              <View style={{ flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 4 }}>
                {TEXT_SCALES.map((value, i) => {
                  const on = i === scaleStep(textScale);
                  return (
                    <Pressable
                      key={value}
                      onPress={() => changeScale(i)}
                      hitSlop={6}
                      accessibilityLabel={`${Math.round(value * 100)}%`}
                      style={{ width: 22, height: 30, alignItems: "center", justifyContent: "center" }}
                    >
                      <View
                        style={{
                          width: on ? 14 : 8,
                          height: on ? 14 : 8,
                          borderRadius: 7,
                          backgroundColor: i <= scaleStep(textScale) ? colors.accent : colors.trackBg,
                        }}
                      />
                    </Pressable>
                  );
                })}
              </View>
              <TextSizeButton disabled={scaleStep(textScale) === TEXT_SCALES.length - 1} onPress={() => changeScale(scaleStep(textScale) + 1)} />
            </View>
            <View style={{ backgroundColor: colors.softBg, borderRadius: 14, padding: 14 }}>
              <AppText weight="500" size={15 * textScale} color={colors.proseInk} style={{ textAlign: "left", writingDirection: "ltr", lineHeight: 15 * textScale * 1.6 }}>
                Hypertension is a common condition in adults.
              </AppText>
            </View>
            <Pressable
              onPress={() => changeScale(TEXT_SCALES.indexOf(1))}
              disabled={scaleStep(textScale) === TEXT_SCALES.indexOf(1)}
              style={{ alignSelf: "center", paddingHorizontal: 16, paddingVertical: 8 }}
            >
              <AppText weight="800" size={13} color={scaleStep(textScale) === TEXT_SCALES.indexOf(1) ? colors.muted : colors.accent}>
                {t("readerTextSizeReset")}
              </AppText>
            </Pressable>
            <AppText weight="600" size={12} muted center style={{ lineHeight: 19 }}>
              {t("highlightsHint")}
            </AppText>
          </Pressable>
        </Pressable>
      </Modal>

      <Modal
        visible={!!graphicId || !!tableView}
        transparent
        animationType="fade"
        onRequestClose={closeAuxiliary}
        supportedOrientations={["portrait", "landscape", "landscape-left", "landscape-right"]}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: tableView ? colors.cardBg : "rgba(4,10,9,0.55)", padding: tableView ? 0 : 16 }}>
          <View style={{ flex: 1, backgroundColor: colors.cardBg, borderRadius: tableView ? 0 : 18, overflow: "hidden" }}>
            <View
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 10,
                paddingHorizontal: 16,
                paddingVertical: tableView ? 4 : 12,
                borderBottomWidth: 1,
                borderBottomColor: colors.sheetLine,
              }}
            >
              <AppText accessibilityRole="header" weight="800" size={13} numberOfLines={2} style={{ flex: 1, writingDirection: "ltr", textAlign: "left" }}>
                {tableView?.title ?? stripHtml(graphicTopic?.title ?? "")}
              </AppText>
              <ChromeButton onPress={closeAuxiliary} size={44} accessibilityLabel={isFa ? "بستن جدول یا تصویر" : "Close table or graphic"}>
                <AppText weight="800" size={14} color={colors.ink}>
                  ×
                </AppText>
              </ChromeButton>
            </View>

            {!tableView && (graphicLoading || (!!graphicTopic && graphicHtml === undefined)) ? (
              <LoadingState />
            ) : !tableView && (graphicTopicError || graphicHtmlError || !graphicTopic) ? (
              <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
                <AppText muted weight="600">
                  {t("uptodateGraphicLoadError")}
                </AppText>
              </View>
            ) : Platform.OS === "web" ? (
              <iframe
                key={tableView ? "table" : "graphic"}
                ref={(node) => { auxiliaryIframeRef.current = node; }}
                srcDoc={auxiliaryHtml}
                style={{ flexGrow: 1, border: "none", width: "100%", height: "100%" }}
                title={tableView?.title ?? stripHtml(graphicTopic?.title ?? "")}
              />
            ) : (
              <WebView
                key={tableView ? "table" : "graphic"}
                originWhitelist={["*"]}
                source={{ html: auxiliaryHtml }}
                onMessage={handleAuxiliaryMessage}
                style={{ flex: 1, backgroundColor: colors.cardBg }}
              />
            )}
          </View>
        </SafeAreaView>
      </Modal>
    </View>
  );
}

/** "Tables 6 · Figures 2 · 14 related topics" under the outline's Related entry. */
function relatedSummary(groups: RelatedGroup[]): string {
  return groups
    .map((g) => (g.heading ? `${g.heading} ${g.items.length}` : g.kind === "calculators" ? `Calculators ${g.items.length}` : `Topics ${g.items.length}`))
    .join(" · ");
}

/** A step button of the in-article find bar: big enough for a thumb. */
function FindStepButton({ glyph, label, disabled, onPress }: { glyph: string; label: string; disabled?: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={label}
      hitSlop={4}
      style={({ pressed }) => ({
        width: 44,
        height: 44,
        borderRadius: 12,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: pressed ? `${colors.accent}22` : colors.cardBg,
        borderWidth: 1,
        borderColor: colors.trackBg,
        opacity: disabled ? 0.4 : 1,
      })}
    >
      <AppText weight="800" size={glyph === "✕" ? 16 : 17} color={disabled ? colors.muted : colors.accent} style={{ lineHeight: 22 }}>
        {glyph}
      </AppText>
    </Pressable>
  );
}

/** "A-" / "A+" of the text-size sheet. */
function TextSizeButton({ small, disabled, onPress }: { small?: boolean; disabled?: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={small ? "A-" : "A+"}
      style={{
        width: 48,
        height: 48,
        borderRadius: 14,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: colors.softBg,
        borderWidth: 1,
        borderColor: colors.trackBg,
        opacity: disabled ? 0.4 : 1,
      }}
    >
      <AppText weight="800" size={small ? 14 : 21} color={colors.accent}>
        A
      </AppText>
    </Pressable>
  );
}
