/** Shared DOM/CSS for the web iframe and native WebView. No source HTML is
 * rewritten on disk; rowspan/colspan and the reader's text offsets survive. */
export type TableLabels = ReturnType<typeof tableLabels>;

export function tableLabels(isFa: boolean) {
  return isFa ? {
    direction: "rtl", open: "نمایش تمام‌صفحهٔ جدول", all: "کل جدول", width: "تمام‌عرض",
    smaller: "کوچک‌نمایی", larger: "بزرگ‌نمایی", zoom: "میزان زوم", notes: "توضیحات و پاورقی‌ها",
    hint: "برای جزئیات زوم کنید؛ برای جابه‌جایی، جدول را بکشید.", unavailable: "جدول در دسترس نیست.",
  } : {
    direction: "ltr", open: "View table full screen", all: "Fit table", width: "Fit width",
    smaller: "Zoom out", larger: "Zoom in", zoom: "Zoom level", notes: "Notes and references",
    hint: "Pinch to zoom. Drag to move around the table.", unavailable: "Table unavailable.",
  };
}

type TableColors = { ink: string; prose: string; muted: string; bg: string; accent: string; rule: string; accentSoft: string };

export function tableStyles(c: TableColors, dark: boolean) {
  return `
  :root { --utd-table-paper:${c.bg}; --utd-table-ink:${c.ink}; --utd-table-muted:${c.muted};
    --utd-table-line:${dark ? "#3a4640" : "#dde5e0"}; --utd-table-soft:${dark ? "#202823" : "#f6f8f7"}; }
  .utd-table-box { margin:18px 0; }
  .utd-table-tools { display:flex; justify-content:flex-end; margin-bottom:8px; }
  .utd-table-button { font:600 13px/1.4 -apple-system,"Segoe UI",sans-serif; min-height:44px;
    padding:8px 12px; border:1px solid var(--utd-table-line); border-radius:6px; cursor:pointer;
    color:var(--utd-table-ink); background:var(--utd-table-paper); white-space:nowrap; }
  .utd-table-button:focus-visible, .utd-table-stage:focus-visible { outline:3px solid ${c.accent}; outline-offset:-3px; }
  .utd-table-button[aria-pressed="true"] { background:var(--utd-table-ink); color:var(--utd-table-paper); }
  .utd-table-button:disabled { opacity:.5; cursor:default; }
  .utd-table-scroll { overflow:auto; max-width:100%; max-height:620px; overscroll-behavior:contain;
    border:1px solid var(--utd-table-line); border-radius:6px; }
  table.utd-reference-table { display:table; border-collapse:separate; border-spacing:0; width:100%;
    min-width:var(--utd-table-min,0px); overflow:visible; table-layout:fixed; direction:ltr; text-align:left;
    font-size:1rem; line-height:1.6; color:${c.prose}; }
  .utd-reference-table > :is(thead,tbody,tfoot) > tr > :is(td,th) {
    border:0; border-right:1px solid var(--utd-table-line); border-bottom:1px solid var(--utd-table-line);
    padding:14px 16px; vertical-align:top; background:var(--utd-table-paper); overflow-wrap:break-word; }
  .utd-reference-table > :is(thead,tbody,tfoot) > tr > :last-child { border-right:0; }
  .utd-reference-table > :is(thead,tbody,tfoot) > tr:last-child > :is(td,th) { border-bottom:0; }
  .utd-reference-table > :is(thead,tbody,tfoot) > .utd-table-heading > :is(td,th) {
    color:var(--utd-table-muted); font-size:.87rem; font-weight:600; border-bottom:2px solid ${c.accent}; }
  .utd-reference-table > :is(thead,tbody,tfoot) > .utd-table-top > :is(td,th) {
    position:sticky; top:var(--utd-head-top,0px); z-index:4; }
  .utd-reference-table > :is(thead,tbody,tfoot) > tr > .utd-table-label {
    position:sticky; left:0; z-index:2; font-weight:600; background:var(--utd-table-soft); }
  .utd-reference-table > :is(thead,tbody,tfoot) > .utd-table-top > .utd-table-label { z-index:6; }
  .utd-reference-table .utd-table-number { text-align:right; font-variant-numeric:tabular-nums; }
  .utd-reference-table p { margin:0 0 9px; }
  .utd-reference-table p:last-child { margin-bottom:0; }
  .utd-reference-table ul { margin:0; padding-left:20px; }
  .utd-reference-table li + li { margin-top:6px; }
  .utd-reference-table[data-columns="4"] > colgroup > col:nth-child(1) { width:27%; }
  .utd-reference-table[data-columns="4"] > colgroup > col:nth-child(2) { width:39%; }
  .utd-reference-table[data-columns="4"] > colgroup > col:nth-child(3) { width:22%; }
  .utd-reference-table[data-columns="4"] > colgroup > col:nth-child(4) { width:12%; }
  html.utd-table-viewer, body.utd-table-viewer { height:100%; overflow:hidden; }
  body.utd-table-viewer { padding:0; }
  body.utd-table-viewer > :not(#utdTableViewer):not(script):not(style) { display:none!important; }
  #utdTableViewer { display:flex; flex-direction:column; height:100%; width:100%; max-width:none; }
  .utd-table-zoom { display:flex; align-items:center; justify-content:center; gap:4px; flex-wrap:wrap;
    padding:8px; flex:none; background:var(--utd-table-paper); border-bottom:1px solid var(--utd-table-line); }
  .utd-table-zoom .utd-table-button { padding:8px 10px; min-width:44px; }
  .utd-table-zoom output { font:600 13px/1.4 -apple-system,"Segoe UI",sans-serif; width:48px;
    text-align:center; font-variant-numeric:tabular-nums; direction:ltr; }
  .utd-table-stage { flex:1; min-height:0; width:100%; overflow:auto; direction:ltr;
    touch-action:none; overscroll-behavior:contain; background:var(--utd-table-soft); cursor:grab; }
  .utd-table-stage:active { cursor:grabbing; }
  body .utd-table-extent { position:relative; max-width:none; min-width:100%; min-height:100%; }
  body .utd-table-canvas { position:absolute; max-width:none; transform-origin:0 0; user-select:none; }
  body .utd-table-canvas * { max-width:none; }
  .utd-table-canvas > table { border:1px solid var(--utd-table-line); }
  .utd-table-canvas > .utd-reference-table > :is(thead,tbody,tfoot) > tr > :is(td,th) { position:static; }
  .utd-table-footer { flex:none; background:var(--utd-table-paper); border-top:1px solid var(--utd-table-line); }
  .utd-table-hint { margin:0; padding:8px 12px; text-align:center; font-size:12px; line-height:1.5; color:var(--utd-table-muted); }
  .utd-table-notes { padding:0 12px 8px; font-size:13px; line-height:1.65; }
  .utd-table-notes summary { min-height:44px; padding-top:8px; cursor:pointer; font-weight:600; }
  .utd-table-notes-content { max-height:28vh; overflow:auto; direction:ltr; text-align:left; padding:8px 4px; }
  `;
}

// String.raw keeps the exact same script on Hermes and in the browser;
// serializing a compiled function via toString() is not supported by Hermes.
export const TABLE_SCRIPT = String.raw`
function __utdTablesInit(options) {
  var labels = options.labels, tables = Array.prototype.filter.call(document.querySelectorAll("table"), function (t) {
    return !t.parentElement.closest("table");
  });
  function button(text, label, action) {
    var b = document.createElement("button"); b.type = "button"; b.className = "utd-table-button";
    b.textContent = text; b.setAttribute("aria-label", label); b.addEventListener("click", action); return b;
  }
  function prepare(table, index) {
    var occupied = [], columns = 0, heads = [], leading = true;
    Array.prototype.forEach.call(table.rows, function (row, r) {
      occupied[r] = occupied[r] || []; var col = 0;
      var heading = row.cells.length > 0 && Array.prototype.every.call(row.cells, function (cell) {
        return cell.tagName === "TH" || /subtitle/.test(cell.className);
      });
      if (heading) row.classList.add("utd-table-heading");
      if (heading && leading) { row.classList.add("utd-table-top"); heads.push(row); }
      else leading = false;
      Array.prototype.forEach.call(Array.from(row.cells), function (original) {
        while (occupied[r][col]) col++;
        var cell = original, span = cell.colSpan || 1, down = cell.rowSpan || 1;
        if (heading && cell.tagName !== "TH") {
          cell = document.createElement("th");
          Array.prototype.forEach.call(original.attributes, function (a) { cell.setAttribute(a.name, a.value); });
          while (original.firstChild) cell.appendChild(original.firstChild);
          original.parentNode.replaceChild(cell, original); cell.scope = span > 1 ? "colgroup" : "col";
        }
        if (col === 0 && span === 1) cell.classList.add("utd-table-label");
        if (/^\d+(?:[.,]\d+)?$/.test(cell.textContent.trim())) cell.classList.add("utd-table-number");
        for (var y = r; y < r + down; y++) {
          occupied[y] = occupied[y] || []; for (var x = col; x < col + span; x++) occupied[y][x] = true;
        }
        col += span; columns = Math.max(columns, col);
      });
    });
    var minimum = columns < 2 ? 0 : columns === 2 ? 600 : columns === 3 ? 780 : Math.max(860, columns * 180);
    var originalWidth = parseFloat(table.getAttribute("width")) || parseFloat(table.style.width) || 0;
    if ((table.getAttribute("width") || table.style.width || "").indexOf("%") >= 0) originalWidth = 0;
    var width = Math.max(minimum, Math.min(2400, originalWidth));
    table.classList.add("utd-reference-table"); table.dataset.columns = columns;
    table.style.setProperty("--utd-table-min", width + "px"); table.style.width = "100%";
    Array.prototype.forEach.call(Array.from(table.children), function (child) {
      if (child.tagName === "COLGROUP" || child.tagName === "COL") child.remove();
    });
    var cols = document.createElement("colgroup");
    for (var c = 0; c < columns; c++) cols.appendChild(document.createElement("col"));
    table.insertBefore(cols, table.firstChild);
    var box = document.createElement("div"); box.className = "utd-table-box";
    var tools = document.createElement("div"); tools.className = "utd-table-tools"; tools.dir = labels.direction;
    tools.setAttribute("data-utd-ui", "");
    var figure = table.closest(".figure,.utdGraphicWrapper,figure");
    var title = table.caption || (figure && figure.querySelector(".ttl,.graphic_title,figcaption"));
    var open = button(labels.open, labels.open, function () {
      __utdEmitOp({ type:"table", index:index, context:options.context, title:title ? title.textContent.trim() : "" });
    });
    tools.appendChild(open);
    var scroll = document.createElement("div"); scroll.className = "utd-table-scroll"; scroll.tabIndex = 0;
    scroll.setAttribute("role", "region"); scroll.setAttribute("aria-label", labels.open);
    table.parentNode.insertBefore(box, table); box.appendChild(tools); box.appendChild(scroll); scroll.appendChild(table);
    function offsets() { var top = 0; heads.forEach(function (row) { row.style.setProperty("--utd-head-top", top + "px"); top += row.offsetHeight; }); }
    if (typeof ResizeObserver !== "undefined") new ResizeObserver(offsets).observe(table);
    offsets();
    return { table:table, width:width };
  }
  var prepared = tables.map(prepare);
  if (!options.viewer) return;
  var selected = prepared[options.viewer.index];
  if (!selected) { document.body.textContent = labels.unavailable; return; }
  var table = selected.table, figure = table.closest(".figure,.utdGraphicWrapper,figure");
  var notes = figure ? Array.from(figure.querySelectorAll(".graphic_lgnd,.graphic_footnotes,.graphic_reference")) : [];
  var root = document.createElement("div"); root.id = "utdTableViewer";
  var toolbar = document.createElement("div"); toolbar.className = "utd-table-zoom"; toolbar.dir = labels.direction;
  toolbar.setAttribute("data-utd-ui", "");
  var stage = document.createElement("div"); stage.className = "utd-table-stage"; stage.tabIndex = 0;
  stage.setAttribute("role", "region"); stage.setAttribute("aria-label", options.viewer.title || labels.open);
  var extent = document.createElement("div"); extent.className = "utd-table-extent";
  var canvas = document.createElement("div"); canvas.className = "utd-table-canvas";
  var naturalWidth = Math.max(selected.width, table.offsetWidth, 320), naturalHeight = 1;
  canvas.style.width = naturalWidth + "px"; canvas.appendChild(table); extent.appendChild(canvas); stage.appendChild(extent);
  var footer = document.createElement("div"); footer.className = "utd-table-footer";
  var hint = document.createElement("p"); hint.className = "utd-table-hint"; hint.dir = labels.direction; hint.textContent = labels.hint; footer.appendChild(hint);
  if (notes.length) {
    var details = document.createElement("details"); details.className = "utd-table-notes";
    var summary = document.createElement("summary"); summary.dir = labels.direction; summary.textContent = labels.notes;
    var content = document.createElement("div"); content.className = "utd-table-notes-content";
    notes.forEach(function (node) { content.appendChild(node); }); details.appendChild(summary); details.appendChild(content); footer.appendChild(details);
  }
  var scale = 1, fitMode = "all", left = 12, top = 12, ready = false;
  var allButton = button(labels.all, labels.all, function () { fit("all"); });
  var widthButton = button(labels.width, labels.width, function () { fit("width"); });
  var smaller = button("−", labels.smaller, function () { zoom(scale / 1.25); });
  var larger = button("+", labels.larger, function () { zoom(scale * 1.25); });
  var output = document.createElement("output"); output.setAttribute("aria-label", labels.zoom); output.setAttribute("aria-live", "polite");
  [allButton, widthButton, smaller, output, larger].forEach(function (node) { toolbar.appendChild(node); });
  root.appendChild(toolbar); root.appendChild(stage); root.appendChild(footer); document.body.appendChild(root);
  document.documentElement.classList.add("utd-table-viewer");
  document.body.classList.add("utd-table-viewer");
  function allScale() { return Math.min(1, (stage.clientWidth - 24) / naturalWidth, (stage.clientHeight - 24) / naturalHeight); }
  function draw(value, anchorX, anchorY, contentX, contentY) {
    var min = Math.max(.001, Math.min(.25, allScale()));
    var next = Math.max(min, Math.min(4, value));
    anchorX = anchorX === undefined ? stage.clientWidth / 2 : anchorX;
    anchorY = anchorY === undefined ? stage.clientHeight / 2 : anchorY;
    contentX = contentX === undefined ? (stage.scrollLeft + anchorX - left) / scale : contentX;
    contentY = contentY === undefined ? (stage.scrollTop + anchorY - top) / scale : contentY;
    scale = next;
    var width = Math.max(stage.clientWidth, naturalWidth * scale + 24), height = Math.max(stage.clientHeight, naturalHeight * scale + 24);
    left = Math.max(12, (width - naturalWidth * scale) / 2); top = Math.max(12, (height - naturalHeight * scale) / 2);
    extent.style.width = width + "px"; extent.style.height = height + "px";
    canvas.style.left = left + "px"; canvas.style.top = top + "px"; canvas.style.transform = "scale(" + scale + ")";
    stage.scrollLeft = contentX * scale + left - anchorX; stage.scrollTop = contentY * scale + top - anchorY;
    output.value = Math.round(scale * 100) + "%";
    smaller.disabled = scale <= min + .0001; larger.disabled = scale >= 4;
    allButton.setAttribute("aria-pressed", String(fitMode === "all")); widthButton.setAttribute("aria-pressed", String(fitMode === "width"));
  }
  function fit(kind) {
    fitMode = kind;
    draw(kind === "all" ? allScale() : Math.min(4, (stage.clientWidth - 24) / naturalWidth));
    stage.scrollLeft = 0; stage.scrollTop = 0;
  }
  function zoom(value, x, y, cx, cy) { fitMode = "manual"; draw(value, x, y, cx, cy); }
  function measure() {
    naturalHeight = Math.max(1, table.offsetHeight);
    if (stage.clientHeight < 25 || stage.clientWidth < 25) return;
    if (!ready || fitMode !== "manual") fit(fitMode === "width" ? "width" : "all"); else draw(scale);
    ready = true;
  }
  var pointers = new Map(), last = null, pinch = null, moved = false, lastTap = 0, ignoreClickUntil = 0;
  function position(e) { var r = stage.getBoundingClientRect(); return { x:e.clientX-r.left, y:e.clientY-r.top }; }
  function beginPinch() {
    var p = Array.from(pointers.values()), x = (p[0].x+p[1].x)/2, y = (p[0].y+p[1].y)/2;
    pinch = { distance:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y), scale:scale,
      x:(stage.scrollLeft+x-left)/scale, y:(stage.scrollTop+y-top)/scale };
  }
  stage.addEventListener("pointerdown", function (e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    pointers.set(e.pointerId, position(e));
    // Preserve a tap's original link target; capture only once dragging starts.
    if (!e.target.closest("a")) stage.setPointerCapture(e.pointerId);
    moved = false; last = position(e); if (pointers.size === 2) { moved = true; beginPinch(); }
  });
  stage.addEventListener("pointermove", function (e) {
    if (!pointers.has(e.pointerId)) return;
    var pos = position(e); pointers.set(e.pointerId, pos);
    if (pointers.size >= 2 && pinch) {
      var p = Array.from(pointers.values()), distance = Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);
      zoom(pinch.scale * distance / Math.max(1,pinch.distance), (p[0].x+p[1].x)/2, (p[0].y+p[1].y)/2, pinch.x, pinch.y); moved = true;
    } else if (last) {
      var dx = pos.x-last.x, dy = pos.y-last.y;
      if (Math.abs(dx)+Math.abs(dy)>1) { moved = true; stage.setPointerCapture(e.pointerId); }
      stage.scrollLeft -= dx; stage.scrollTop -= dy; last = pos;
    }
    e.preventDefault();
  });
  function endPointer(e) {
    if (!pointers.has(e.pointerId)) return;
    if (moved) ignoreClickUntil = Date.now()+400;
    if (!moved && e.type !== "pointercancel" && e.pointerType === "touch") {
      if (Date.now()-lastTap < 300) { if (fitMode === "all") zoom(Math.max(1,scale*2)); else fit("all"); lastTap=0; }
      else lastTap=Date.now();
    }
    pointers.delete(e.pointerId); pinch=null; last=pointers.size ? Array.from(pointers.values())[0] : null;
  }
  stage.addEventListener("pointerup", endPointer); stage.addEventListener("pointercancel", endPointer);
  stage.addEventListener("click", function (e) { if (Date.now()<ignoreClickUntil) { e.preventDefault(); e.stopPropagation(); } }, true);
  stage.addEventListener("dblclick", function (e) { if (e.pointerType === "touch") return; e.preventDefault(); if (fitMode === "all") zoom(Math.max(1,scale*2)); else fit("all"); });
  stage.addEventListener("wheel", function (e) {
    if (!e.ctrlKey) return; e.preventDefault(); var p=position(e); zoom(scale*Math.exp(-e.deltaY*.01),p.x,p.y);
  }, { passive:false });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { __utdEmitOp({ type:"table-close" }); return; }
    if (e.key === "+" || e.key === "=") { e.preventDefault(); zoom(scale*1.25); }
    if (e.key === "-") { e.preventDefault(); zoom(scale/1.25); }
    if (e.key === "0") { e.preventDefault(); fit("all"); }
  });
  if (typeof ResizeObserver !== "undefined") { var observer=new ResizeObserver(measure); observer.observe(stage); observer.observe(table); }
  window.addEventListener("resize", measure); document.fonts && document.fonts.ready.then(measure); requestAnimationFrame(measure);
  // Expose only interaction helpers for the shared reader and regression checks.
  window.__utdTableView = { fit:fit, zoom:zoom, state:function () { return {scale:scale,mode:fitMode,width:naturalWidth,height:naturalHeight}; } };
}
`;
