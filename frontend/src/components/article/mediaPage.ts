/**
 * The full-screen page an article image or table opens into (MediaViewer):
 * a self-contained HTML document, drawn in an <iframe> on the web and a
 * WebView on the phone, showing the image at its full stored quality or the
 * table at its natural width -- not squeezed into the article's column --
 * with pinch, double-tap and wheel zoom and dragging to pan.
 *
 * The zoom is the page's own script, not the browser's: a page zoom inside an
 * iframe would zoom the whole app around it on a phone's browser, and the
 * same script gives the WebView the same gestures.
 */

export type MediaContent =
  | { kind: "image"; src: string; alt: string; caption: string }
  | { kind: "table"; headers: string[] | null; rows: string[][]; caption: string };

export interface MediaPageColors {
  background: string;
  ink: string;
  muted: string;
  headerBg: string;
  line: string;
  cellBg: string;
}

const escape = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// Pointer-driven zoom and pan of #content inside #stage. The content is
// first fitted to the stage (an image whole, a table to its width); from
// there it zooms 1x..8x around the fingers or the tap, and pans only as far
// as there is content to show.
const ZOOM_SCRIPT = `
(function () {
  var stage = document.getElementById("stage");
  var content = document.getElementById("content");
  var fit = 1, s = 1, x = 0, y = 0, MAX = 8;
  var pointers = {}, last = null, lastTap = 0;

  function bounds() {
    var w = content.offsetWidth * fit * s, h = content.offsetHeight * fit * s;
    var W = stage.clientWidth, H = stage.clientHeight;
    return { w: w, h: h, W: W, H: H };
  }
  function clamp() {
    var b = bounds();
    x = b.w <= b.W ? (b.W - b.w) / 2 : Math.min(0, Math.max(b.W - b.w, x));
    y = b.h <= b.H ? (b.H - b.h) / 2 : Math.min(0, Math.max(b.H - b.h, y));
  }
  function draw() {
    clamp();
    content.style.transform = "translate(" + x + "px," + y + "px) scale(" + fit * s + ")";
  }
  function zoomAt(next, px, py) {
    next = Math.max(1, Math.min(MAX, next));
    var k = next / s;
    x = px - (px - x) * k;
    y = py - (py - y) * k;
    s = next;
    draw();
  }
  function refit() {
    var W = stage.clientWidth, H = stage.clientHeight;
    var cw = content.offsetWidth, ch = content.offsetHeight;
    if (!cw || !ch) return;
    fit = document.body.dataset.kind === "table" ? Math.min(1, W / cw) : Math.min(W / cw, H / ch, 2);
    // a large image can zoom to 3x its own pixels, not just 8x its fit
    MAX = Math.max(8, 3 / fit);
    if (document.body.dataset.kind === "table") { x = 0; y = 0; }
    draw();
  }

  stage.addEventListener("pointerdown", function (e) {
    stage.setPointerCapture(e.pointerId);
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    last = null;
    var now = Date.now();
    if (Object.keys(pointers).length === 1 && now - lastTap < 300) {
      zoomAt(s > 1.05 ? 1 : 2.5, e.clientX, e.clientY);
      lastTap = 0;
    } else {
      lastTap = now;
    }
  });
  stage.addEventListener("pointermove", function (e) {
    if (!pointers[e.pointerId]) return;
    var prev = pointers[e.pointerId];
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    var ids = Object.keys(pointers);
    if (ids.length === 2) {
      var a = pointers[ids[0]], b = pointers[ids[1]];
      var d = Math.hypot(a.x - b.x, a.y - b.y), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      if (last) {
        x += mx - last.mx;
        y += my - last.my;
        zoomAt(s * (d / last.d), mx, my);
      }
      last = { d: d, mx: mx, my: my };
    } else if (ids.length === 1) {
      x += e.clientX - prev.x;
      y += e.clientY - prev.y;
      draw();
    }
  });
  function lift(e) { delete pointers[e.pointerId]; last = null; }
  stage.addEventListener("pointerup", lift);
  stage.addEventListener("pointercancel", lift);
  stage.addEventListener("wheel", function (e) {
    e.preventDefault();
    zoomAt(s * Math.exp(-e.deltaY / 300), e.clientX, e.clientY);
  }, { passive: false });
  window.addEventListener("resize", refit);
  var img = content.querySelector("img");
  if (img && !img.complete) img.addEventListener("load", refit);
  refit();
})();
`;

function page(kind: MediaContent["kind"], body: string, c: MediaPageColors): string {
  return `<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<style>
  html, body { margin: 0; height: 100%; background: ${c.background}; color: ${c.ink};
    font-family: -apple-system, "Segoe UI", Roboto, Vazirmatn, sans-serif; }
  #stage { position: fixed; inset: 0; overflow: hidden; touch-action: none; cursor: grab; }
  #content { position: absolute; left: 0; top: 0; transform-origin: 0 0; }
  img { display: block; max-width: none; user-select: none; -webkit-user-drag: none; }
  table { border-collapse: collapse; background: ${c.cellBg}; font-size: 14px; line-height: 1.45; margin: 12px; }
  th, td { border: 1px solid ${c.line}; padding: 8px 10px; text-align: left; vertical-align: top; max-width: 320px; }
  th { background: ${c.headerBg}; font-weight: 800; }
  caption { caption-side: bottom; color: ${c.muted}; font-size: 12px; padding: 8px 2px; text-align: left; }
</style></head>
<body data-kind="${kind}"><div id="stage"><div id="content">${body}</div></div>
<script>${ZOOM_SCRIPT}</script></body></html>`;
}

export function mediaPage(media: MediaContent, colors: MediaPageColors): string {
  if (media.kind === "image") {
    return page("image", `<img src="${media.src}" alt="${escape(media.alt)}">`, colors);
  }
  const head = media.headers
    ? `<thead><tr>${media.headers.map((h) => `<th>${escape(h)}</th>`).join("")}</tr></thead>`
    : "";
  const body = media.rows.map((r) => `<tr>${r.map((cell) => `<td>${escape(cell)}</td>`).join("")}</tr>`).join("");
  const caption = media.caption ? `<caption>${escape(media.caption)}</caption>` : "";
  return page("table", `<table>${caption}${head}<tbody>${body}</tbody></table>`, colors);
}
